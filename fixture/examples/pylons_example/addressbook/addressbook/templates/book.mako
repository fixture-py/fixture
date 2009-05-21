<h2>
Address Book
</h2>

% for person in c.persons:
    <h3>${person.name}</h3>
    <h4>${person.email}</h4>
    % for address in person.my_addresses:
    <h4>${address.address}</h4>
    % endfor
% endfor
