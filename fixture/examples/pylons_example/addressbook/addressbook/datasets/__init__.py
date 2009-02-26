
from fixture import DataSet

class AddressData(DataSet):
    class joe_in_montego:
        address = "111 St. James St, Montego Bay, Jamaica"
    class joe_in_ny:
        address = "111 S. 2nd Ave, New York, NY"

class PersonData(DataSet):
    class joe_gibbs:
        name = "Joe Gibbs"
        email = "joe@joegibbs.com"
        my_addresses = [
            AddressData.joe_in_montego, 
            AddressData.joe_in_ny]