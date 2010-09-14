from Acquisition import aq_parent
from Products.LinguaPlone.public import AlreadyTranslated

def translateFiles(object, event):
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
                    log = getLogger('cs.board.subscribers.file')
                    log.info('Document already translated')


    
