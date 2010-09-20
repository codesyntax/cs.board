from Acquisition import aq_parent
from Products.LinguaPlone.public import AlreadyTranslated
from Products.CMFCore.utils import getToolByName

def translateDocuments(object, event):
    parent = aq_parent(object)
    if parent.portal_type == 'Board':
        translations = parent.getTranslations()
        for lang, translated in translations.items():
            if lang != object.Language():
                try:
                    object.addTranslation(language=lang,
                                          title=object.Title())
                except AlreadyTranslated:
                    from logging import getLogger
                    log = getLogger('cs.board.subscribers.boarddocument')
                    log.info('BoardDocument already translated')


def publishDocument(object, event):
    wtool = getToolByName(object, 'portal_workflow')
    if event.action == 'publish':
        for lang, translated in object.getTranslations().items():
            status = translated[1]            
            if status == 'private':
                trans_obj = translated[0]
                wtool.doActionFor(trans_obj, 'publish')
            else:
                from logging import getLogger
                log = getLogger('cs.board.subscribers.boarddocument')
                log.info('Already published')

    elif event.action == 'retract':
        for lang, translated in object.getTranslations().items():
            status = translated[1]            
            if status == 'published':
                trans_obj = translated[0]
                wtool.doActionFor(trans_obj, 'retract')
            else:
                from logging import getLogger
                log = getLogger('cs.board.subscribers.boarddocument')
                log.info('Already private')
        
    else:
        from logging import getLogger
        log = getLogger('cs.board.subscribers.boarddocument')
        log.info('status == %s' % status)

        
