from zope.interface import implements, Interface

from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from cs.board import boardMessageFactory as _


class IBoardView(Interface):
    """
    Board view interface
    """

    def getPublishedDocuments():
        """ Published documents on the board """


    def getPrivateDocuments():
        """ Private documents on the board """


class BoardView(BrowserView):
    """
    Board browser view
    """
    implements(IBoardView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def getPublishedDocuments(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   portal_type='BoardDocument',
                                   review_state='published')


    def getPrivateDocuments(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   portal_type='BoardDocument',
                                   review_state='private')
