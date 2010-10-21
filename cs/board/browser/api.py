"""
wsapi4plone.core based WS API for document publication
"""

from zope.interface import Interface, implements
from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from DateTime import DateTime
import base64
import ZSI

from soaplib.service import SoapServiceBase, soapmethod
from soaplib.serializers.clazz import ClassSerializer
from soaplib.serializers.primitive import String, Array, Integer
from soaplib.serializers.binary import Attachment

# XXX Remove this before going into production
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl import getSecurityManager
from AccessControl.User import UnrestrictedUser


class IBoardAPI(Interface):

    def wsdl():
        """ return WSDL description of this web service """

    def publish_document(action,
                         filenum,
                         filetype,
                         title_es,
                         title_eu,
                         publication_date,
                         expiration_date,
                         documents=[{'document':'',
                                     'description_es':'',
                                     'description_eu':''},
                                    ]
                         ):
        """
        publish a document on the board
        @param action    - one of INSERT, UPDATE, ADD, DELETE
        @param filenum   - file number
        @param filetype  - file type
        @param title_es  - file title in spanish
        @param title_eu  - file title in basque
        @param publication_date - self explaining 
        @param expiration_date  - self explainain 
        @param documents - a list of documents with its description in basque and spanish

        
        """

    def get_filetype_info(filetype):
        """
        return all the information associated with the indicated type

        @param filetype - file type
        """


    def get_file_info(filenumber):
        """
        return all the information associated with the indicated number

        @param filenum - file number
        """

class DocumentInfo(ClassSerializer):
    class types:
        url_es = String
        url_eu = String

    def __init__(self, name, url_es='', url_eu=''):
        self.name = name
        self.url_es = url_es
        self.url_eu = url_eu

    def __str__(self):
        return str((self.name, self.url_es, self.url_eu))

DocumentInfo.typecode = ZSI.TC.Struct(DocumentInfo,
                                      (ZSI.TC.String('url_es'),
                                       ZSI.TC.String('url_eu'),),
                                      'DocumentInfo')


class FileInfo(ClassSerializer):
    class types:
        description_es = String
        description_eu = String
        document = Attachment

    def __init__(self, name, description_es='', description_eu='', document = None):
        self.name = name
        self.description_es = description_es
        self.description_eu = description_eu
        self.document = document

    def __str__(self):
        return str((self.name, self.description_es))

FileInfo.typecode = ZSI.TC.Struct(FileInfo,
                                  (ZSI.TC.String('description_es'),
                                   ZSI.TC.String('description_eu'),
                                   ZSI.TC.Base64Binary('document')),
                                  'FileInfo')



class MarkerService(SoapServiceBase):

    @soapmethod(String, String, String, String, String, String, String, Array(FileInfo), _returns=Integer)
    def publish_document(self, action='', filenumber='', filetype='',
                         title_es='', title_eu='', publication_date='', expiration_date='',
                         documents=[{'document': '',
                                     'document_filename': '',
                                     'description_es':'',
                                     'description_eu':''},
                                    ],):
        pass

    @soapmethod(String, _returns=Array(DocumentInfo))
    def get_filetype_info(self, filetype):
        pass

    @soapmethod(String, _returns=Array(DocumentInfo))
    def get_file_info(self, filenumber):
        pass

class BoardAPI(BrowserView):
    implements(IBoardAPI)

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')


    def wsdl(self):
        res = self.request.RESPONSE
        res.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        return SoapServiceBase.wsdl(MarkerService(), self.context.absolute_url())

    def publish_document(self, action='', filenumber='', filetype='',
                         title_es='', title_eu='', publication_date='', expiration_date='',
                         documents=[{'document': '',
                                     'document_filename': '',
                                     'description_es':'',
                                     'description_eu':''},
                                    ],):
        """
        action = INSERT | UPDATE | ADD | DELETE
        """

        current_user = getSecurityManager().getUser()
        newSecurityManager(None, UnrestrictedUser('andago', '', ['Manager'], []))

        wtool = getToolByName(self.context, 'portal_workflow')

        if action == 'INSERT':
            id = self.context.generateUniqueId('BoardDocument')
            obj_id = self.context.invokeFactory(id=id,
                                             type_name='BoardDocument',
                                             title=title_es,
                                             filenumber=filenumber,
                                             filetype=filetype)
            obj = getattr(self.context, obj_id)
            obj.setEffectiveDate(DateTime(publication_date))
            obj.setExpirationDate(DateTime(expiration_date))
            obj._renameAfterCreation()
            obj.reindexObject()
            obj_eu = obj.addTranslation(language='eu', title=title_eu)
            obj_eu._renameAfterCreation()
            obj_eu.reindexObject()
            for document in documents:
                doc_id = obj.generateUniqueId('File')
                
                doc_id = obj.invokeFactory(id=doc_id,
                                           type_name='File',
                                           title=document['description_es'],
                                           file=base64.decodestring(document['document']),
                                           filename=document.get('document_filename', ''),
                                           )
                doc_obj = getattr(obj, doc_id)
                doc_obj._renameAfterCreation()
                doc_obj_eu = doc_obj.addTranslation(language='eu', title=document['description_eu'])
                doc_obj_eu._renameAfterCreation()
                doc_obj_eu.reindexObject()

            wtool.doActionFor(obj, 'publish')
            # XXX
            newSecurityManager(None, current_user)
            return 1
                
        elif action == 'UPDATE':
            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         language='es')
            for brain in brains:
                obj = brain.getObject()
                obj.edit(title=title_es,
                         filetype=filetype,
                         filenumber=filenumber,
                         )
                obj.setEffectiveDate(DateTime(publication_date))
                obj.setExpirationDate(DateTime(expiration_date))
                obj.reindexObject()
                obj_eu = obj.getTranslation('eu')
                obj_eu.setTitle(title_eu)
                obj_eu.reindexObject()

            # XXX
            newSecurityManager(None, current_user)
            return 1

        elif action == 'ADD':
            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         Language='es')
            for brain in brains:
                obj = brain.getObject()
                for document in documents:
                    doc_id = obj.generateUniqueId('File')
                    doc_id = obj.invokeFactory(id=doc_id,
                                               type_name='File',
                                               title=document['description_es'],
                                               file=document['document'].data,
                                               filename=document['document_filename'],
                                               )
                    doc_obj = getattr(obj, doc_id)
                    doc_obj._renameAfterCreation()
                    doc_obj_eu = doc_obj.addTranslation(language='eu', title=document['description_eu'])
                    doc_obj_eu._renameAfterCreation()
                    doc_obj_eu.reindexObject()
            # XXX
            newSecurityManager(None, current_user)
            return 1

        elif action == 'DELETE':
            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         Language='es')
            for brain in brains:
                obj = brain.getObject()
                obj_eu = obj.getTranslation('eu')
                del aq_parent(obj)[obj.getId()]
                del aq_parent(obj_eu)[obj_eu.getId()]

            # XXX
            newSecurityManager(None, current_user)
            return 1

        else:
            # XXX
            newSecurityManager(None, current_user)
            return 500

        # XXX
        newSecurityManager(None, current_user)

            
            
    def get_filetype_info(self, filetype):
        current_user = getSecurityManager().getUser()
        newSecurityManager(None, UnrestrictedUser('andago', '', ['Manager'], []))
        ret =  self.decorateBrains(self.portal_catalog(filetype=filetype, portal_type='BoardDocument', Language='es'))

        newSecurityManager(None, current_user)
        return ret

    def get_file_info(self, filenumber):
        current_user = getSecurityManager().getUser()
        newSecurityManager(None, UnrestrictedUser('andago', '', ['Manager'], []))
        ret = self.decorateBrains(self.portal_catalog(filenumber=filenumber, portal_type='BoardDocument', Language='es'))

        newSecurityManager(None, current_user)
        return ret


    def decorateBrains(self, brains):
        ret = []
        for brain in brains:
            ret.append(self.decorateBrain(brain))

        return ret

    def decorateBrain(self, brain):
        data = {}
        obj = brain.getObject()
        obj_eu = obj.getTranslation('eu')
        ## data['title_es'] = brain.Title
        ## data['title_eu'] = obj_eu.Title()
        ## data['filenumber'] = brain.filenumber
        ## data['filetype'] = brain.filetype
        ## data['publication_date'] = brain.EffectiveDate
        ## data['expiration_date'] = brain.ExpirationDate
        data['url_es'] = brain.getURL()
        data['url_eu'] = obj_eu.absolute_url()
        ## data['documents'] = []
       
        ## document_view = getMultiAdapter((obj, self.request), name='view')
        ## for f in document_view.files():
        ##     f_obj = f.getObject()
        ##     file_data = {}
        ##     file_data['description_es'] = f.Title
        ##     file_data['description_eu'] = f_obj.getTranslation('eu').Title()
        ##     file_data['document'] = xmlrpclib.Binary(f_obj.data)
        ##     file_data['document_filename'] = f_obj.getField('file').getFilename(f_obj)
        ##     data['documents'].append(file_data)

        return data
        


                                  
