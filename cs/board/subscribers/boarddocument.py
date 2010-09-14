from Acquisition import aq_parent
from Products.LinguaPlone.public import AlreadyTranslated

def translateFiles(object, event):
    # event.oldParent
    # event.oldName
    # event.newParent
    # event.newName
    #import pdb;pdb.set_trace()
    parent = aq_parent(object)
    if parent.portal_type == 'BoardDocument':
        translations = parent.getTranslations()
        for lang, translated in translations.items():
            if lang != object.Language():
                try:
                    object.addTranslation(language=lang,
                                          title=object.Title())
                except AlreadyTranslated:
                    from logging import getLogger
                    log = getLogger('cs.board.subscriber.boarddocument')
                    log.info('Document already translated')


    
        
