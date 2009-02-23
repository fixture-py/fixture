from fixture import DjangoFixture
from fixtures import *
from util import *
from fixture.style import NamedDataStyle
from nose.tools import raises
from project.app import models

def _check_row(medium, column_vals):
    medium._check_schema(column_vals)
    
def test_schema_conformance():
    
    valid_rels = ValidNoRelationsData()
    invalid_rels = InvalidNoRelationsData()
    
    for dataset, model, callable in \
                [
                    (valid_rels,  models.NoRelations, _check_row),
                    (invalid_rels, models.NoRelations,
                                    raises(ValueError)(_check_row))
                ]:
        djm = DjangoFixture.DjangoMedium(models.NoRelations, dataset)
        rows = [(row[0], list(get_column_vals(row[1]))) for row in dataset]
        for row in rows:
            callable.description = "schema.conformance: %s %s in %s" % (row[0], row[1],
                                                    dataset.__class__.__name__)
            yield callable, djm, row[1]
            
    