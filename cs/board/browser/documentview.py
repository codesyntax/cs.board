from zope.interface import implements, Interface
from Acquisition import aq_inner

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from cs.board import boardMessageFactory as _


class IDocumentView(Interface):
    """
    Document view interface
    """
    def files():
        """ Get files of this document """

class DocumentView(BrowserView):
    """
    Document browser view
    """
    implements(IDocumentView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def files(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   portal_type=['File'])
