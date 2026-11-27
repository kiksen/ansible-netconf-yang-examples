


Netconfproblme: CSCwk32801


%DMI-6-NETCONF_SSH_INFO: Switch 1 R0/0: ncsshd_bp: NETCONF/SSH: [pid(24154)] WARNING: Using self-signed trustpoint for netconf hostkey is deprecated. Please generate dedicated netconf SSH keypair instead.

# Is used in exec now, not in config mode anymore
switch# crypto key generate rsa label NETCONF-KEY modulus 4096

# bind new keypair to netconf-yang
switch(config)# netconf-yang ssh server keypair NETCONF-KEY



Du meinst vermutlich die operation-Attribute von <edit-config> (RFC 6241). Davon gibt es fünf:

Operation	Verhalten
merge	Daten werden in die bestehende Konfiguration eingemischt. Das ist der Default.
replace	Der Knoten wird ersetzt. Existiert er nicht, wird er angelegt.
create	Der Knoten wird nur angelegt. Existiert er schon, gibt es den Fehler data-exists.
delete	Der Knoten wird gelöscht. Existiert er nicht, gibt es den Fehler data-missing.
remove	Der Knoten wird gelöscht. Existiert er nicht, passiert nichts und es gibt keinen Fehler.

Ergänzend gibt es auf <edit-config>-Ebene:

default-operation mit den Werten merge, replace oder none. none ändert nur Knoten, die explizit ein operation-Attribut tragen.
test-option (Capability :validate) mit test-then-set, set oder test-only.
error-option mit stop-on-error, continue-on-error oder rollback-on-error.

Die NETCONF-Protokolloperationen selbst sind:

Basis (RFC 6241): <get>, <get-config>, <edit-config>, <copy-config>, <delete-config>, <lock>, <unlock>, <close-session> und <kill-session>.
Optionale Capabilities: <commit>, <cancel-commit> und <discard-changes> (:candidate), <validate> (:validate).
Weitere RFCs: <get-schema> (RFC 6022), <create-subscription> (RFC 5277), <get-data> und <edit-data> (RFC 8526, NMDA).