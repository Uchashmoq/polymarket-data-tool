# Polymarket Data Tool
a polymarket tool to fetch orderbook data
## Init 
`pip instal requests websockets python-socks sortedcontainers `
## Files
`data/<event_slug>/info.json:`
```json
{
   "$schema":"https://gamma-api.polymarket.com/schemas/Event.json",
   "slug":"highest-temperature-in-paris-on-june-28-2026",
   "markets":[
      {
         "conditionId":"0xb5c1fe53668a26b507316827e122590ae1c340176ea182ef199b7b2aef266fac",
         "slug":"highest-temperature-in-paris-on-june-28-2026-27corbelow",
         "clobTokenIds":"[\"27948609818500875324626583570922144926746651108316399731108734866735947036264\", \"104825787337777782214053435519909313382237972255819693442111260118497682593972\"]",
         //...
      },
    //...
   ],
   //...
}
```
`data/<event_slug>/<market_slug>/ws_raw_jsonl.gz:`

every line is a json

book event:
```json
{
   "market":"0x9b7d078fa902071b87ea5c1a3cc451adc82141956d0d75c9aee0efa6578f097d", //condition id of market
   "asset_id":"53827085893420955881949754956302117244886379463448979473557489934517732900299",
   "timestamp":"1782634152631",
   "hash":"dba700eb423a7cccaf10c6192c9b6cc3c94ae31c",
   "bids":[
      {
         "price":"0.001",
         "size":"124.01"
      },
      //...
   ],
   "asks":[
      //...
   ],
   "tick_size":"0.001",
   "event_type":"book",
   "last_trade_price":"0.999"
}
```

price change event:
```json
{
   "market":"0x9b7d078fa902071b87ea5c1a3cc451adc82141956d0d75c9aee0efa6578f097d",//condition id of market
   "price_changes":[
      {
         "asset_id":"25554635279956744876547757443671901513367609937900931336720615105029892759310",
         "price":"0.001",
         "size":"209.25",
         "side":"SELL",
         "hash":"91a038ce4957b820e05c7ee46835e07605f8077d",
         "best_bid":"0",
         "best_ask":"0.001"
      },
      {
         "asset_id":"53827085893420955881949754956302117244886379463448979473557489934517732900299",
         "price":"0.999",
         "size":"209.25",
         "side":"BUY",
         "hash":"ce37e287c0582d52b457d8ff750340a614407357",
         "best_bid":"0.999",
         "best_ask":"1"
      }
   ],
   "timestamp":"1782634156761",
   "event_type":"price_change"
}

```