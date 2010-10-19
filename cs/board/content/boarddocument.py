"""Definition of the BoardDocument content type
"""

from zope.interface import implements

try:
    from Products.LinguaPlone import public as atapi
except ImportError:
    from Products.Archetypes import atapi
    
from Products.ATContentTypes.content import folder
from Products.ATContentTypes.content import schemata

# -*- Message Factory Imported Here -*-
from cs.board import boardMessageFactory as _

from cs.board.interfaces import IBoardDocument
from cs.board.config import PROJECTNAME

BoardDocumentSchema = folder.ATFolderSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-
    atapi.StringField('filenumber',
                      required = True,
                      searchable = True,
                      languageIndependent = True,
                      storage = atapi.AnnotationStorage(),
                      widget = atapi.StringWidget(
                                    label = _(u'label_filenumber', default=u'File number'),
                                    )
        ),
    atapi.StringField('filetype',
                      required = True,
                      searchable = True,
                      languageIndependent = True,
                      storage = atapi.AnnotationStorage(),                      
                      widget = atapi.StringWidget(
                                    label = _(u'label_filetype', default=u'File type'),
                                    )
        ),
   

))

# Set storage on fields copied from ATFolderSchema, making sure
# they work well with the python bridge properties.
BoardDocumentSchema['title'].widget.label = _(u'label_literalprocedure', default=u'Literal procedure name')
BoardDocumentSchema['description'].widget.visible['edit'] = 'invisible'
BoardDocumentSchema['title'].storage = atapi.AnnotationStorage()
BoardDocumentSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(
    BoardDocumentSchema,
    folderish=True,
    moveDiscussion=False
)

# Move dates to main schemata. finalizeSchemata moves them to 'dates'
BoardDocumentSchema.changeSchemataForField('effectiveDate', 'default')
BoardDocumentSchema.changeSchemataForField('expirationDate', 'default')


class BoardDocument(folder.ATFolder):
    """Document published on the board"""
    implements(IBoardDocument)

    meta_type = "BoardDocument"
    schema = BoardDocumentSchema

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    filenumber = atapi.ATFieldProperty('filenumber')
    filetype = atapi.ATFieldProperty('filetype')

atapi.registerType(BoardDocument, PROJECTNAME)
