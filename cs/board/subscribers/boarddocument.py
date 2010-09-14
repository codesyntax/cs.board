from Products.CMFCore.utils import getToolByName

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

        
