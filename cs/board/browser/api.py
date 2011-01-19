from zope import event
from zope.interface import Interface, implements
from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from Products.CMFPlone.utils import safe_unicode

from Products.Archetypes.event import ObjectInitializedEvent

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


def safe_utf8(data):
    return safe_unicode(data).encode('utf-8')

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
                                     'description_eu':'',
                                     'filename':''},
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

    def __init__(self, url_es='', url_eu=''):
        self.url_es = url_es
        self.url_eu = url_eu

    def __str__(self):
        return str((self.url_es, self.url_eu))

DocumentInfo.typecode = ZSI.TC.Struct(DocumentInfo,
                                      (ZSI.TC.String('url_es'),
                                       ZSI.TC.String('url_eu'),),
                                      'DocumentInfo',
                                      type=('cs.board.browser.api.MarkerService', 'DocumentInfo'))


class FileInfo(ClassSerializer):
    class types:
        description_es = String
        description_eu = String
        document = Attachment
        filename = String

    def __init__(self, description_es='', description_eu='', document = None, filename=''):
        self.description_es = description_es
        self.description_eu = description_eu
        self.document = document
        self.filename = filename

FileInfo.typecode = ZSI.TC.Struct(FileInfo,
                                  (ZSI.TC.String('description_es'),
                                   ZSI.TC.String('description_eu'),
                                   ZSI.TC.Base64Binary('document'),
                                   ZSI.TC.String('filename')),
                                  'FileInfo',
                                  type=('cs.board.browser.api.MarkerService', 'FileInfo'),)


class MarkerService(SoapServiceBase):

    @soapmethod(String, String, String, String, String, String, String, Array(FileInfo), _returns=Integer)
    def publish_document(self, action='', filenumber='', filetype='',
                         title_es='', title_eu='', publication_date='', expiration_date='',
                         documents=[{'document': '',
                                     'filename': '',
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
                                     'filename': '',
                                     'description_es':'',
                                     'description_eu':''},
                                    ],):
        """
        action = INSERT | UPDATE | ADD | DELETE
        """

        current_user = getSecurityManager().getUser()
        newSecurityManager(None, UnrestrictedUser('andago', '', ['Manager'], []))

        wtool = getToolByName(self.context, 'portal_workflow')


        from logging import getLogger
        log = getLogger('cs.board.api')

        

        if action == 'INSERT':
            # Validation
            if not filenumber:
                raise ZSI.Fault(ZSI.Fault.Client, 'filenumber is required')
            if not filetype:
                raise ZSI.Fault(ZSI.Fault.Client, 'filetype is required')
            if not title_es:
                raise ZSI.Fault(ZSI.Fault.Client, 'title_es is required')
            if not title_eu:
                raise ZSI.Fault(ZSI.Fault.Client, 'title_eu is required')
            if not publication_date:
                raise ZSI.Fault(ZSI.Fault.Client, 'publication_date is required')
            if not expiration_date:
                raise ZSI.Fault(ZSI.Fault.Client, 'expiration_date is required')

            try:
                pd = DateTime(publication_date)
            except Exception,e:
                raise ZSI.Fault(ZSI.Fault.Client, 'publication_date format is not correct: %s' % e)

            try:
                ed = DateTime(expiration_date)
            except Exception,e:
                raise ZSI.Fault(ZSI.Fault.Client, 'expiration_date format is not correct: %s' % e)

            if pd > ed:
                raise ZSI.Fault(ZSI.Fault.Client, 'expiration_date must be later than the publication_date' % e)

            # end of validation                 
                
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
            try:
                obj_eu = obj.addTranslation(language='eu', title=title_eu)
            except:
                # Translation errors
                raise ZSI.Fault(ZSI.Fault.Client, 'error occured when creating translation of the item. Contact the administrator.')
            
            obj_eu._renameAfterCreation()
            obj_eu.reindexObject()

            # Create the file for each published            
            if documents:
                for document in documents.values():
                    self.generate_document(obj, document)

            wtool.doActionFor(obj, 'publish')
            # XXX
            newSecurityManager(None, current_user)
            return 1
                
        elif action == 'UPDATE':
            if not filenumber:
                raise ZSI.Fault(ZSI.Fault.Client, 'You have to provide the filenumber to identify the document')
            
            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         language='es')
            for brain in brains:
                obj = brain.getObject()
                if title_es:
                    obj.edit(title=title_es)
                if filetype:
                    obj.edit(filetype=filetype)

                ## XXX: it doesn't make sense to edit the filenumber
                ## if we've used it to identify it :
                    
                ## if filenumber:
                ##     obj.edit(filenumber=filenumber)

                try:
                    if publication_date:
                        obj.setEffectiveDate(DateTime(publication_date))
                except:
                    raise ZSI.Fault(ZSI.Fault.Client, 'publication_date format is not correct')

                try:
                    if expiration_date:
                        obj.setExpirationDate(DateTime(expiration_date))
                except:
                    raise ZSI.Fault(ZSI.Fault.Client, 'expiration_date format is not correct')

                obj.reindexObject()
                if title_eu:
                    obj_eu = obj.getTranslation('eu')
                    obj_eu.setTitle(title_eu)
                    obj_eu.reindexObject()

            # XXX
            newSecurityManager(None, current_user)
            return 1

        elif action == 'ADD':
            if not filenumber:
                raise ZSI.Fault(ZSI.Fault.Client, 'You have to provide the filenumber to identify the document')

            if not documents:
                raise ZSI.Fault(ZSI.Fault.Client, 'You have to provide the files to add to the document')
            
            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         Language='es')
            for brain in brains:
                obj = brain.getObject()
                for document in documents.values():
                    self.generate_document(obj, document)

            # XXX
            newSecurityManager(None, current_user)
            return 1

        elif action == 'DELETE':
            if not filenumber:
                raise ZSI.Fault(ZSI.Fault.Client, 'You have to provide the filenumber to identify the document')

            brains = self.portal_catalog(filenumber=filenumber,
                                         portal_type='BoardDocument',
                                         Language='es')
            for brain in brains:
                try:
                    obj = brain.getObject()
                    obj_eu = obj.getTranslation('eu')
                    del aq_parent(obj)[obj.getId()]
                    del aq_parent(obj_eu)[obj_eu.getId()]
                except:
                    raise ZSI.Fault(ZSI.Fault.Client, 'An error occurred while deleting the document. Contact the administrator.')

            # XXX
            newSecurityManager(None, current_user)
            return 1

        else:
            # XXX
            newSecurityManager(None, current_user)
            return 500

        # XXX
        newSecurityManager(None, current_user)

    def generate_document(self, obj, document):

        from logging import getLogger
        log = getLogger('cs.board.api.generate_document')
        
        if document.get('document', None) is None:
            raise ZSI.Fault(ZSI.Fault.Client, 'document is required')

        doc_id = obj.generateUniqueId('AccreditedFile')

        try:
            filecontent = base64.decodestring(document.get('document', ''))
        except:
            raise ZSI.Fault(ZSI.Fault.Client, 'an error occured when decoding the base64 encoded file content')

        try:
            doc_id = obj.invokeFactory(id=doc_id,
                                       type_name='AccreditedFile',
                                       title=document.get('description_es', ''),
                                       file=filecontent,
                                       filename=safe_utf8(document.get('filename', '')),
                                       )

            doc_obj = getattr(obj, doc_id)
            ff = doc_obj.getField('file')
            ff.setFilename(doc_obj, safe_utf8(document.get('filename',document.get('description_es', ''))))
            doc_obj._renameAfterCreation()
            doc_obj_eu = doc_obj.addTranslation(language='eu', title=document.get('description_eu', ''))
            doc_obj_eu._renameAfterCreation()
            doc_obj_eu.reindexObject()
            event.notify(ObjectInitializedEvent(doc_obj))
            event.notify(ObjectInitializedEvent(doc_obj_eu))
            log.info('created')
        except:
            raise ZSI.Fault(ZSI.Fault.Client, 'An error occured while adding the file. Contact the administrator.')
            
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

        return ret #, ZSI.TC.Array(('cs.board.browser.api.MarkerService', 'DocumentInfoArray'), DocumentInfo.typecode, 'DocumentInfoArray', mutable=True)

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
        ##     file_data['filename'] = f_obj.getField('file').getFilename(f_obj)
        ##     data['documents'].append(file_data)

        return DocumentInfo(url_es=data['url_es'],
                            url_eu=data['url_eu'])
        


                                  
