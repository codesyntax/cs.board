"""Definition of the Board content type
"""

from zope.interface import implements

try:
    from Products.LinguaPlone import public as atapi
except ImportError:
    from Products.Archetypes import atapi
    
from Products.ATContentTypes.content import folder
from Products.ATContentTypes.content import schemata

# -*- Message Factory Imported Here -*-

from cs.board.interfaces import IBoard
from cs.board.config import PROJECTNAME

BoardSchema = folder.ATFolderSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-

))

# Set storage on fields copied from ATFolderSchema, making sure
# they work well with the python bridge properties.

BoardSchema['title'].storage = atapi.AnnotationStorage()
BoardSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(
    BoardSchema,
    folderish=True,
    moveDiscussion=False
)


class Board(folder.ATFolder):
    """Document publication board"""
    implements(IBoard)

    meta_type = "Board"
    schema = BoardSchema

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-

atapi.registerType(Board, PROJECTNAME)
