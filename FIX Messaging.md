footer: Zuhlke Engineering Singapore
slidenumbers: true

# Purpose
This tech talk is for engineers with little or no prior knowledge on FIX. It aims to provide a basic understanding of FIX message structure, type of message, message flow and the programming model.

---

# [fit] _
# [fit] What is `FIX`?

---

# [fit] Financial Information eXchange

A messaging standard for the real time electronic exchange of securities transaction data.
---

'20170309 11:41:49.133 - 8=FIXT.1.1^A9=908^A35=y^A49=FIXEDGE^A56=UILNDRGW1^A34=2239^A52=20170309-11:41:49.132^A560=0^A393=1^A320=23387919276913833^A322=23387919276913833_37^A1151=NDF.AFRICA^A893=Y^A146=1^A55=NDF.USD.UGX.10M^A460=0^A423=106^A32030=0^A32237=17^A32278=1^A32277=1^A32239=2^A32292=1^A32042=0^A32321=1^A32322=2^A32354=1^A32045=2^A32047=10^A32053=2^A32296=309^A32054=0^A32055=1000000^A32352=0^A32355=0^A32356=0^A32357=3^A32358=0^A32359=0^A32360=1^A32361=1^A32362=1^A32316=0^A32344=2^A32404=0^A167=NDF^A762=Variable Start End Date^A965=1^A32223=20170309^A32240=D^A32041=D^A32043=20170313^A32353=20170313^A32046=M^A32048=None^A32050=20180113^A32051=20180116^A32345=REUTERS^A32346=ZMWFIX=TR^A32347=USD^A32348=20180112^A32349=20180112^A32302=11:30:00^A562=0.1^A1140=50^A561=0.05^A32243=1^A32331=500000^A454=2^A455=UGX 10M.NS^A456=3^A455=ForeignExchange:NDF^A456=100^A32293=3^A32044=USD^A32044=UGX^A32044=WKNDS^A32294=3^A32052=USD^A32052=UGX^A32052=WKNDS^A1310=1^A1301=FX.AFRICA^A1205=1^A1206=0^A1207=1500^A1208=0.0001^A1237=1^A40=2^A10=251^A2

---

# Who uses FIX?

- Institutional investors (the buy side)
- Broker/dealers (the sell side)
- Exchanges & ECNs
- Financial industry utilities
- Software & services vendors

---

#  What is it used for?
- It’s used by exchanges, ECNs, & brokers/ dealers to distribute market data, quotes, etc.
- Money mangers use it to send orders and receive executions from brokers.
- It’s used by exchanges & ECNs to receive orders or quotes & report trades.
- It’s used to allocate & confirm trades. These are only a few examples.

---

# A brief history of FIX
 1992 1st used between Fidelity & Salomon
 Jan 1995 - FIX 2.7
 Public spec released  Now obsolete
Dec 1995 – FIX 3.0  Now obsolete
1996 – FIX 4.0
 Good US equity support  Still in use in US
1998 – FIX 4.1
 Incremental release
 2000 – FIX 4.2
 Futures, options, FX 2001 – FIX 4.3
 Fixed income, XML 2003 – FIX 4.4
 Confirms & trade reporting
2006 – FIX 5.0 & T1.1
 Complex FX, improved session/transport level

---

# How is the standard governed?
- It’s a public domain standard
- Owned & managed by FIX Protocol, Ltd
- It’s a non-profit financial community organization
- Couple hundred member firms
- Volunteers from member firms & industry work on the specification

---

# Why do we talk about `FIX`?

---

It will also touch base on the populate open-source FIX library: QuickFixJ.

---

# [fit] ⌘+C ⌘+V = :v: