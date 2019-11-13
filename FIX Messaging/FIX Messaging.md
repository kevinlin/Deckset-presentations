autoscale: true
footer: Zuhlke Engineering Singapore
slidenumbers: true

# Why do we talk about FIX?

This tech talk is for engineers with little or no prior knowledge on FIX. 
It aims to provide a basic understanding of FIX message structure, type of message, message flow and the programming model.

---

# [fit] _
# [fit] What is FIX?

---

# [fit] Financial Information eXchange

A messaging standard for the real time electronic exchange of securities transaction data.

---

`8=FIXT.1.1^A9=908^A35=y^A49=FIXEDGE^A56=UILNDRGW1^A34=2239^A52=20170309-11:41:49.132^A560=0^A393=1^A320=23387919276913833^A322=23387919276913833_37^A1151=NDF.AFRICA^A893=Y
^A146=1^A55=NDF.USD.UGX.10M^A460=0^A423=106^A32030=0^A32237=17^A32278=1^A32277=1^A32239=2^A32292=1^A32042=0^A32321=1^A32322=2^A32354=1^A32045=2^A32047=10^A32053=2^A32296=309^A32054=0^A32055=1000000^A32352=0^A32355=0^A32356=0^A32357=3^A32358=0^A32359=0^A32360=1^A32361=1^A32362=1^A32316=0^A32344=2^A32404=0^A167=NDF^A762=Variable Start End Date^A965=1^A32223=20170309^A32240=D^A32041=D^A32043=20170313^A32353=20170313^A32046=M^A32048=None^A32050=20180113^A32051=20180116^A32345=REUTERS^A32346=ZMWFIX=TR^A32347=USD^A32348=20180112^A32349=20180112^A32302=11:30:00^A562=0.1^A1140=50^A561=0.05^A32243=1^A32331=500000^A454=2^A455=UGX 10M.NS^A456=3^A455=ForeignExchange:NDF^A456=100^A32293=3^A32044=USD^A32044=UGX^A32044=WKNDS^A32294=3^A32052=USD^A32052=UGX^A32052=WKNDS^A1310=1^A1301=FX.AFRICA^A1205=1^A1206=0^A1207=1500^A1208=0.0001^A1237=1^A40=2^A10=251^A2`

---

# A brief history of FIX
- Introduced in **1992**
- **1995** - first public spec (FIX 2.7) released
- **1996** - FIX 4.0
    - Introduced with good US equity support (still in use in US)
- **2000** – FIX 4.2
    - Better international support
    - Futures, options, FX
- **2001** – FIX 4.3
    - Fixed income
- **2003** – FIX 4.4
    - Confirmations & trade reporting
- **2006** – FIX 5.0 & FIXT1.1
    - Complex FX, improved session/transport level

---

# Characteristic of FIX
- Simple, field-based messages
- Platform and Transport independent
- Public standard
    - Owned & managed by [FIX Protocol Ltd](https://www.fixtrading.org/)
    - A non-profit financial community organization
- Wide support and lots of software vendors availability 
- Yet very much extensible

---

# Who uses FIX?

- Institutional investors (the buy side)
- Broker/dealers (the sell side)
- Exchanges & ECNs
- Financial industry utilities
- Software & services vendors

---

# What/where is it used?
- Financial Products Supported
    - Equities
    - Fixed Income
    - FX
    - Derivatives (Options, Futures, IR Swaps etc)
- Used worldwide
    - Except China

---

#  What is it used for?
- It’s used by exchanges, ECNs, & brokers/ dealers to distribute market data, quotes, etc.
- Money mangers use it to send orders and receive executions from brokers.
- It’s used by exchanges & ECNs to receive orders or quotes & report trades.
- It’s used to allocate & confirm trades. These are only a few examples.

---

![inline](FIX Architecture.png)

Typical architecture of FIX systems used in the market

---

# Session & application layers
- Session layer/protocol
    - Make & terminate connections
    - Deliver messages in sequence w/ data integrity
- Application layer
    - Business level messages
- Session & application layers decoupled from FIX 5.0 onwards. Tightly coupled prior to that.

---

# FIX Encodings
- tagvalue (classic FIX)
- FAST - FIX Adapted for Streaming
    - Binary encoding for reduced bandwidth use and low latency 
- FIXML - XML
- Extension
  - Public extentions (5000 <= tag number < 9999)
  - External user defined fields have a  and < 9999.
  - Internal customised (tag number >= 10000)
    
---

# Application Messages

- Pre-trade messages
     – Market Data, Security Info etc
- Trade Messages
    – Single Orders, Basket/List Orders, Multi-leg orders, Executions, Order Cancel, Cancel/Replace, Status etc
- Post-Trade Messages
    – Allocations, Settlement Instructions, Positions Management etc

---

# FIX message structure
- Header fields
    - message type, length, sequence number, sender/target, encoding, etc.
- Body fields
    - session & application data
- Trailer fields
    - Signature, checksum

---

# Message fields
- For each field the specification defines:
    - Tag – A unique number.
    - Field Name – Field name with no spaces.
    - Data Type – String, char, price, qty, etc.
    - Description – Definition of data.

--- 

# Tag=Value syntax
- 4 components to each field `<Tag>=<Value><Delimiter>`
    - `<Tag>` is the tag number of the field
    - `=`
    - `<Value>` is the value of the field
    - `<Delimiter>` is ASCII SOH character
    
---

## Buy 5000 IBM @ 110.75

### `8=FIX.4.2^9=251^35=D^49=AFUNDMGR^56=ABROKER^34=2^52=20030615-01:14:49^11=12345^21=1^55=IBM^54=1^60=2003061501:14:49^38=5000^40=2^44=110.75^10=127`

| Header fields | Body fields | Trailer Fields
| --- | --- | --- |
| 8=BeginString (indicates FIX 4.2) | 11=ClOrderID (client order id) | 10=Checksum |
| 9=BodyLength | 21=HandleInst (automated exec) | |
| 35=MsgType (new order) | 55=Symbol (IBM) | |
| 49=SenderCompID (AFUNDMGR) | 54=Side (buy) | |
| 56=TargetCompID (ABROKER) | 56=TransactTime | |
| 34=MsgSeqNum (2) | 38=OrderQty (5000) | |
| 52=SendTime | 40=OrdType (Limit) | |
| | 44=Price (110.75) | |
| | 52=SendTime | |

---

It will also touch base on the populate open-source FIX library: QuickFixJ.

---

## How FIX messaging looks between Buyside/Customer and Sellside/Supplier.

![inline, original](FIX%20System%20Connectivity%20Diagram.png)

---

FIX Dictionary

[](https://www.onixs.biz/fix-dictionary.html)

---

# [fit] ⌘+C ⌘+V = :v: