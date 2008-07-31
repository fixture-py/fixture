
import sys
import unittest
from fixture.util import start_debug, stop_debug
from fixture import DataSet
from fixture.loadable import EnvLoadableFixture
import datetime

class TestComplexLoadQueue(unittest.TestCase):
    def setUp(self):
        start_debug("fixture.loadable.tree")
        pass
    def tearDown(self):
        stop_debug("fixture.loadable.tree")
        pass
    def test_circular_dependencies(self):
        """TestComplexLoadQueue.test_circular_dependencies
        
        ensures the order for unloading objects is correct when objects depend 
        other objects in circular ways.  this long chain was causing a strange 
        bug in the sorting algorithm
        """
        
        #### here's a complex load that was confusing the unload order.
        #### it looked like:
        
        # /--------EventLogData (0)
        #   |__..ActivityLogData (1)
        #     |__..LinkRequestData (2)
        #       |__..CampaignsData (3)
        #         |__..PartnerChannelsData (4)
        #           |__..PartnersData (5)
        #             |__..ContactsData (6)
        #               |__..StatusData (7)
        #             |__..StatusData (6)
        #           |__..StatusData (5)
        #         |__..InternalCommissionSchedData (4)
        #           |__..StatusData (5)
        #         |__..PartnerInsertOrdersData (4)
        #           |__..StatusData (5)
        #         |__..OffersData (4)
        #           |__..ProductsData (5)
        #             |__..ClientsData (6)
        #               |__..ContactsData (7)
        #                 |__..StatusData (8)
        #               |__..ClientTypesData (7)
        #               |__..StatusData (7)
        #           |__..ClientCompensationCalcData (5)
        #             |__..StatusData (6)
        #         |__..PartnerCommissionCalcData (4)
        #           |__..StatusData (5)
        #         |__..ContactsData (4)
        #           |__..StatusData (5)
        #       |__..ClientsData (3)
        #         |__..ContactsData (4)
        #           |__..StatusData (5)
        #         |__..ClientTypesData (4)
        #         |__..StatusData (4)
        #   |__..OffersData (1)
        #     |__..ProductsData (2)
        #       |__..ClientsData (3)
        #         |__..ContactsData (4)
        #           |__..StatusData (5)
        #         |__..ClientTypesData (4)
        #         |__..StatusData (4)
        #     |__..ClientCompensationCalcData (2)
        #       |__..StatusData (3)
        #   |__..ClientEventTypeData (1)
        #     |__..ClientsData (2)
        #       |__..ContactsData (3)
        #         |__..StatusData (4)
        #       |__..ClientTypesData (3)
        #       |__..StatusData (3)
        #     |__..EventClassData (2)
        
        class StatusData(DataSet):
            class status_1:
                id = 1
                value = 'uninitialized'
            class status_2:
                id = 2
                value = 'deleted'
            class status_3:
                id = 3
                value = 'proposed'
            class status_4:
                id = 4
                value = 'approved'
            class status_5:
                id = 5
                value = 'active'
            class status_6:
                id = 6
                value = 'terminated'
            class status_7:
                id = 7
                value = 'ended'
            class status_8:
                id = 8
                value = 'revoked'

        class ClientTypesData(DataSet):
            class client_types_2:
                type = 'real'
                id = 2

        class ContactsData(DataSet):
            class contacts_1682:
                status = StatusData.status_1.ref('id')
            class contacts_1742:
                status = StatusData.status_1.ref('id')
            class contacts_1779:
                status = StatusData.status_1.ref('id')
            class contacts_5091:
                status = StatusData.status_1.ref('id')
            class contacts_5099:
                status = StatusData.status_1.ref('id')
            class contacts_5176:
                status = StatusData.status_1.ref('id')
            class contacts_5177:
                status = StatusData.status_1.ref('id')
            class contacts_5200:
                status = StatusData.status_1.ref('id')
            class contacts_5543:
                status = StatusData.status_1.ref('id')
            class contacts_5720:
                status = StatusData.status_1.ref('id')
            class contacts_5421:
                status = StatusData.status_1.ref('id')

        class PartnersData(DataSet):
            class partners_2131:
                status = StatusData.status_1.ref('id')
                primary_contact_id = ContactsData.contacts_5177.ref('id')
                remit_to_contact_id = ContactsData.contacts_5176.ref('id')
                lfo_media_ops_id = ContactsData.contacts_5200.ref('id')
            class partners_1988:
                status = StatusData.status_1.ref('id')
                primary_contact_id = ContactsData.contacts_1682.ref('id')
                remit_to_contact_id = ContactsData.contacts_1682.ref('id')
                lfo_media_ops_id = ContactsData.contacts_5091.ref('id')
            class partners_2418:
                status = StatusData.status_1.ref('id')
                primary_contact_id = ContactsData.contacts_5720.ref('id')
                remit_to_contact_id = ContactsData.contacts_5720.ref('id')
                lfo_media_ops_id = ContactsData.contacts_5543.ref('id')

        class PartnerChannelsData(DataSet):
            class partner_channels_1468:
                status = StatusData.status_1.ref('id')
                partner_id = PartnersData.partners_2131.ref('id')
            class partner_channels_1563:
                status = StatusData.status_1.ref('id')
                partner_id = PartnersData.partners_1988.ref('id')
            class partner_channels_2000:
                status = StatusData.status_1.ref('id')
                partner_id = PartnersData.partners_2418.ref('id')

        class InternalCommissionSchedData(DataSet):
            class internal_commission_sched_1:
                status = StatusData.status_1.ref('id')

        class PartnerInsertOrdersData(DataSet):
            class partner_insert_orders_4248:
                status = StatusData.status_1.ref('id')
            class partner_insert_orders_3946:
                status = StatusData.status_1.ref('id')

        class ClientCompensationCalcData(DataSet):
            class client_compensation_calc_3:
                status = StatusData.status_1.ref('id')
            class client_compensation_calc_4:
                status = StatusData.status_1.ref('id')

        class ClientsData(DataSet):
            class clients_106:
                status = StatusData.status_1.ref('id')
                primary_contact_id = ContactsData.contacts_5099.ref('id')
                client_type_id = ClientTypesData.client_types_2.ref('id')
                account_manager_id = ContactsData.contacts_5421.ref('id')

        class EventClassData(DataSet):
            class event_class_1:
                id = 1
            class event_class_2:
                id = 2
            class event_class_3:
                id = 3
            class event_class_5:
                id = 5
            class event_class_6:
                id = 6

        class ClientEventTypeData(DataSet):
            class acme_click:
                event_class_id = EventClassData.event_class_1.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 10
            class acme_submit:
                event_class_id = EventClassData.event_class_2.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 11
            class acme_confirmation:
                event_class_id = EventClassData.event_class_3.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 12
            class acme_cancel:
                event_class_id = EventClassData.event_class_3.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 13
            class acme_install:
                event_class_id = EventClassData.event_class_5.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 14
            class acme_failure:
                event_class_id = EventClassData.event_class_3.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 15
            class acme_bonus:
                event_class_id = EventClassData.event_class_6.ref('id')
                client_id = ClientsData.clients_106.ref('id')
                id = 16

        class ProductsData(DataSet):
            class products_132:
                client_id = ClientsData.clients_106.ref('id')
                id = 132
            class products_12:
                client_id = ClientsData.clients_106.ref('id')
                id = 12
            class products_56:
                client_id = ClientsData.clients_106.ref('id')
                id = 56
            class products_120:
                client_id = ClientsData.clients_106.ref('id')
                id = 120
            class products_121:
                client_id = ClientsData.clients_106.ref('id')
                id = 121
            class products_122:
                client_id = ClientsData.clients_106.ref('id')
                id = 122
            class products_123:
                client_id = ClientsData.clients_106.ref('id')
                id = 123
            class products_56:
                client_id = ClientsData.clients_106.ref('id')
                id = 56
            class products_61:
                client_id = ClientsData.clients_106.ref('id')
                id = 61
            class acme_hidefup_product:
                client_id = ClientsData.clients_106.ref('id')
                id = 62

        class OffersData(DataSet):
            class acme_ii_offer:
                product_id = ProductsData.products_12.ref('id')
                calc_id = \
                 ClientCompensationCalcData.client_compensation_calc_3.ref('id')
                id = 304
            class offers_13:
                product_id = ProductsData.products_12.ref('id')
                calc_id = \
                 ClientCompensationCalcData.client_compensation_calc_4.ref('id')
            class offers_829:
                product_id = ProductsData.products_123.ref('id')
                id = 829
            class acme_default_hsd_offer:
                product_id = ProductsData.products_12.ref('id')
                id = 888
            class acme_default_digi_offer:
                product_id = ProductsData.products_56.ref('id')
                id = 845
            class acme_hidefup_default_offer:
                product_id = ProductsData.acme_hidefup_product.ref('id')
                id = 853

        class PartnerCommissionCalcData(DataSet):
            class partner_commission_calc_16:
                status = StatusData.status_1.ref('id')

        class CampaignsData(DataSet):
            class campaigns_50805:
                internal_commission_id = \
              InternalCommissionSchedData.internal_commission_sched_1.ref('id')
                orig_offer_id = OffersData.acme_ii_offer.ref('id')
                partner_commission_id = \
                  PartnerCommissionCalcData.partner_commission_calc_16.ref('id')
                io_id = \
                  PartnerInsertOrdersData.partner_insert_orders_4248.ref('id')
                salesperson_id = ContactsData.contacts_1779.ref('id')
                channel_id = PartnerChannelsData.partner_channels_1468.ref('id')
            class campaigns_50199:
                internal_commission_id = \
            InternalCommissionSchedData.internal_commission_sched_1.ref('id')
                orig_offer_id = OffersData.offers_13.ref('id')
                pcomm = \
                  PartnerCommissionCalcData.partner_commission_calc_16.ref('id')
                io_id = \
                  PartnerInsertOrdersData.partner_insert_orders_3946.ref('id')
                salesperson_id = ContactsData.contacts_1742.ref('id')
                channel_id = PartnerChannelsData.partner_channels_1563.ref('id')
            class campaigns_55310:
                internal_commission_id = \
              InternalCommissionSchedData.internal_commission_sched_1.ref('id')
                orig_offer_id = OffersData.offers_829.ref('id')
                salesperson_id = ContactsData.contacts_5543.ref('id')
                channel_id = PartnerChannelsData.partner_channels_2000.ref('id')

        class LinkRequestData(DataSet):
            class link_request_52084:
                campaign_id = CampaignsData.campaigns_50805.ref('id')
                client_id = ClientsData.clients_106.ref('id')
            # acme default link ...
            class link_request_51439:
                campaign_id = CampaignsData.campaigns_50199.ref('id')
                client_id = ClientsData.clients_106.ref('id')
            class link_request_56477:
                campaign_id = CampaignsData.campaigns_55310.ref('id')
                client_id = ClientsData.clients_106.ref('id')

        class ActivityLogData(DataSet):
            class activity_log_6540907:
                link_id = LinkRequestData.link_request_56477.ref('id')

        class EventLogData(DataSet):
            class acme_click_event:
                activity_id = ActivityLogData.activity_log_6540907.ref('id')
                closing_offer_id = OffersData.offers_829.ref('id')
                event_type_id = ClientEventTypeData.acme_click.ref('id')
            class acme_submit_event(acme_click_event):
                event_type_id = ClientEventTypeData.acme_submit.ref('id')
            class acme_install_event(acme_click_event):
                event_type_id = ClientEventTypeData.acme_install.ref('id')
        
        cleared_datasets = []
        
        class NoOpMedium(EnvLoadableFixture.StorageMediumAdapter):
            """a stub medium that saves nothing and doesn't complain"""
            def __getattr__(self, name): return True
            def clear(self, obj): pass
            def clearall(self):
                cleared_datasets.append(self.dataset)
                super(NoOpMedium, self).clearall()
            def save(self, row, column_vals): pass
        class NoOpFixture(EnvLoadableFixture):
            """a fixture that pretends to load stuff but doesn't really."""
            def attach_storage_medium(self, ds): 
                ds.meta.storage_medium = NoOpMedium(None, ds)
            def rollback(self): pass
            def commit(self): pass
        
        fixture = NoOpFixture(medium=NoOpMedium)
        data = fixture.data(EventLogData)
        data.setup()
        data.teardown()
        # print [d.__class__.__name__ for d in cleared_datasets]
        
        class ds(object):
            """class name of a dataset."""
            def __init__(self, name):
                self.name = name
            def was_cleared_before(self, other):
                """assert this dataset was cleared before another."""
                cleared_other = False
                cleared_self = False
                for d in cleared_datasets:
                    name = d.__class__.__name__
                    if name == other.name:
                        cleared_other = True
                    if name == self.name:
                        cleared_self = True
                        if not cleared_other:
                            return True
                        else:
                            assert False, "%s was not cleared before %s" % (
                                                        self.name, other.name) 
                assert cleared_other, "%s was never cleared" % other.name
                assert cleared_self, "%s was never cleared" % self.name
        
        ds('OffersData').was_cleared_before(ds('ProductsData'))
        ds('ProductsData').was_cleared_before(ds('ClientsData'))
        ds('CampaignsData').was_cleared_before(ds('OffersData'))
        