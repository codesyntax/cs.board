from Products.CMFCore.utils import getToolByName

class BoardContentReindexer:

    def __init__(self, portal):
        self.portal = portal

    def reindex(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        catalog.reindexIndex(['filenumber', 'filetype'], self.portal.REQUEST)

def importVarious(context):
    """ Board Catalog reindexer after installation """
    if context.readDataFile('cs.board_various.txt') is None:
        return

    site = context.getSite()
    gen = BoardContentReindexer(site)
    gen.reindex()
    
