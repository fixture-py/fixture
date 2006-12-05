
from sqlobject import *
    
class FxtCategory(SQLObject):
    name = StringCol()

class FxtProduct(SQLObject):
    name = StringCol()
    category = ForeignKey('FxtCategory')

class FxtOffer(SQLObject):
    name = StringCol()
    category = ForeignKey('FxtCategory')
    product = ForeignKey('FxtProduct')