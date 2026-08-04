# Menneskelig sjekkliste før ekstern bruk

Den automatiske sjekken (`scripts/check_brand.py`) fanger det maskinelt
målbare. Denne listen fanger det den ikke kan: skjønn, kontekst og faglig
kvalitet. Gå gjennom punktene før dekket sendes ut av huset – helst en annen
person enn den som laget dekket.

## Budskap og struktur

- [ ] Tittelrekken kan leses alene som et sammenhengende resonnement (action titles)
- [ ] Ett budskap per slide – ingen slide prøver å si to ting
- [ ] Åpningen svarer på «hvorfor er vi her», avslutningen på «hva nå»
- [ ] Tall og påstander er riktige, kildeført der det trengs, og konsistente
      med andre leveranser til samme mottaker

## Design og merkevare

- [ ] Helhetsinntrykk: ser dette ut som BDO – varme og nærhet med
      profesjonalitet, ikke polert konkurrentuttrykk?
- [ ] Rød brukes som aksent, ikke som teppefarge over innholdsslides
- [ ] Grafene: riktig grafttype for budskapet, innsikten i tittelen,
      lesbare akser, ingen pynt uten funksjon
- [ ] Foto følger fotoreglene (ekte, nære, norske miljøer, mangfold)
- [ ] Ingen tekst-overflow eller overlapp – sjekk rendrede bilder, ikke bare
      XML (Trebuchet er QA-upålitelig i forhåndsvisning)

## Kontekst og jus

- [ ] Kundenavn, logoer og tall som ikke skal deles videre, er fjernet ved
      gjenbruk av gamle slides
- [ ] Konfidensialitetsmerking der det er relevant
- [ ] Språket følger norsk-analysesprak-registeret (eller er konsist engelsk
      hvis mottaker krever det)

Avvik som går igjen her, men som aldri fanges av check_brand.py, er signal om
at sjekken bør utvides – meld det inn via skill-evaluator-prosessen.
