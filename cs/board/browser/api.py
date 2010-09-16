"""
wsapi4plone.core based WS API for document publication
"""

from zope.interface import Interface, implements
from zope.component import getMultiAdapter
from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from wsapi4plone.core.browser.wsapi import WSAPI

from DateTime import DateTime
import xmlrpclib


class IBoardAPI(Interface):
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



class BoardAPI(WSAPI):
    implements(IBoardAPI)

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

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

        wtool = getToolByName(self.context, 'portal_workflow')

        if action == 'INSERT':
            id = self.context.generateUniqueId('BoardDocument')
            obj_id = self.context.invokeFactory(id=id,
                                             type_name='BoardDocument',
                                             title=title_es,
                                             filenumber=filenumber,
                                             filetype=filetype,
                                             EffectiveDate=DateTime(publication_date),
                                             ExpirationDate=DateTime(expiration_date))
            obj = getattr(self.context, obj_id)
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
                                           file=document['document'].data,
                                           filename=document['document_filename'],
                                           )
                doc_obj = getattr(obj, doc_id)
                doc_obj._renameAfterCreation()
                doc_obj_eu = doc_obj.addTranslation(language='eu', title=document['description_eu'])
                doc_obj_eu._renameAfterCreation()
                doc_obj_eu.reindexObject()

            wtool.doActionFor(obj, 'publish')
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
                         EffectiveDate=DateTime(publication_date),
                         ExpirationDate=DateTime(expiration_date),
                         )
                obj_eu = obj.getTranslation('eu')
                obj_eu.setTitle(title_eu)

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

            return 1

        else:
            return 500

            
            

    def get_filetype_info(self, filetype):
        return self.decorateBrains(self.portal_catalog(filetype=filetype, portal_type='BoardDocument', Language='es'))

    def get_file_info(self, filenumber):
        return self.decorateBrains(self.portal_catalog(filenumber=filenumber, portal_type='BoardDocument', Language='es'))


    def decorateBrains(self, brains):
        ret = []
        for brain in brains:
            ret.append(self.decorateBrain(brain))

        return ret

    def decorateBrain(self, brain):
        data = {}
        obj = brain.getObject()
        obj_eu = obj.getTranslation('eu')
        data['title_es'] = brain.Title
        data['title_eu'] = obj_eu.Title()
        data['filenumber'] = brain.filenumber
        data['filetype'] = brain.filetype
        data['publication_date'] = brain.EffectiveDate
        data['expiration_date'] = brain.ExpirationDate
        data['url_es'] = brain.getURL()
        data['url_eu'] = obj_eu.absolute_url()
        data['documents'] = []
       
        document_view = getMultiAdapter((obj, self.request), name='view')
        for f in document_view.files():
            f_obj = f.getObject()
            file_data = {}
            file_data['description_es'] = f.Title
            file_data['description_eu'] = f_obj.getTranslation('eu').Title()
            file_data['document'] = xmlrpclib.Binary(f_obj.data)
            file_data['document_filename'] = f_obj.getField('file').getFilename(f_obj)
            data['documents'].append(file_data)

        return data
        


                                  
