
from fixture import DataSet

class AddressData(DataSet):
    class joe_in_kingston:
        address = "111 Maple Ave, Kingston, Jamaica"
    class joe_in_ny:
        address = "111 S. 2nd Ave, New York, NY"

class PersonData(DataSet):
    class joe_gibbs:
        name = "Joe Gibbs"
        email = "joe@joegibbs.com"
        my_addresses = [
            AddressData.joe_in_kingston, 
            AddressData.joe_in_ny]