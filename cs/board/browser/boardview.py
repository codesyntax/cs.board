from zope.interface import implements, Interface

from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from DateTime import DateTime
from plone.memoize.view import memoize

class IBoardView(Interface):
    """
    Board view interface
    """

    def getPublishedDocuments():
        """ Published documents on the board """

    def getPublishedExpiredDocuments():
        """ Published but expired documents on the board """

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

    @memoize
    def getPublishedDocuments(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   effective={'query': DateTime(),
                                              'range': 'max'},
                                   expires={'query': DateTime(),
                                            'range': 'min'},
                                   sort_on='effective',
                                   sort_order='reverse',
                                   portal_type='BoardDocument',
                                   review_state='published')

    @memoize
    def getPublishedExpiredDocuments(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   expires={'query': DateTime(),
                                            'range': 'max'},
                                   sort_on='effective',
                                   sort_order='reverse',
                                   portal_type='BoardDocument',
                                   review_state='published')

    @memoize
    def getPrivateDocuments(self):
        context = aq_inner(self.context)
        return self.portal_catalog(path='/'.join(context.getPhysicalPath()),
                                   sort_on='created',
                                   portal_type='BoardDocument',
                                   review_state='private')

