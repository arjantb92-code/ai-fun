# Bulk Transacties & Soft Delete - Test Checklist

## Migratie

- [ ] Run `cd backend && flask db upgrade` (PostgreSQL moet draaien)
- [ ] Controleer dat de `deleted_at` kolom bestaat in de `transactions` tabel

## Soft Delete

- [ ] Verwijder een transactie → krijgt `deleted_at` timestamp
- [ ] Verwijderde transactie verschijnt niet meer in normale lijst
- [ ] Probeer een afgerekende transactie te verwijderen → 403 error

## Prullenbak

- [ ] Open "Prullenbak" tab in frontend
- [ ] Verwijderde transacties worden getoond met `deleted_at` datum
- [ ] Klik "Herstel" → transactie terug in normale lijst
- [ ] Klik "Definitief verwijderen" → bevestiging → echt weg

## Bulk Selectie

- [ ] Klik op transactie checkbox → wordt geselecteerd (rode rand)
- [ ] Selecteer meerdere transacties
- [ ] Bulk toolbar verschijnt met aantal geselecteerde
- [ ] "Opheffen" knop werkt (selectie leegmaken)

## Bulk Splits

- [ ] Open "Zelfde personen toepassen" modal
- [ ] Toggle personen aan/uit
- [ ] Verhoog/verlaag gewichten
- [ ] Klik "Toepassen" → splits worden bijgewerkt voor alle geselecteerde transacties
- [ ] Toast melding verschijnt met aantal bijgewerkt

## Bulk Verwijderen

- [ ] Selecteer meerdere transacties
- [ ] Klik "Verwijderen" → bevestiging
- [ ] Alle geselecteerde transacties naar prullenbak
- [ ] Toast melding verschijnt

## Afrekening Geschiedenis

- [ ] Open "Balans" tab
- [ ] Bekijk afrekening geschiedenis met "Toon posten" knop
- [ ] Klik op knop → transacties uitklappen
- [ ] Per transactie: omschrijving, bedrag, betaald door, datum/tijd

## Edge Cases

- [ ] Afgerekende transacties kunnen niet soft-deleted worden
- [ ] Alleen items in prullenbak kunnen permanent verwijderd worden
- [ ] Bulk update slaat afgerekende/verwijderde transacties over
- [ ] Balansberekening negeert soft-deleted transacties

---

## Voorgestelde Commit Message

```
feat: bulk transacties, soft delete en prullenbak

Backend:
- Add deleted_at column to Transaction model for soft delete
- Add migration 4a5b6c7d8e9f for deleted_at column
- Add _tx_not_deleted helper to filter soft-deleted transactions
- Update all transaction queries to exclude soft-deleted items
- Modify DELETE /transactions/<id> for soft delete (403 for settled)
- Add POST /transactions/<id>/restore endpoint
- Add DELETE /transactions/<id>/permanent endpoint
- Add GET /transactions?deleted=true for trash view
- Add PATCH /transactions/bulk endpoint for bulk updates
- Update GET /settlements/history to include transactions per settlement

Frontend:
- Add deletedTransactions and fetchTrash to appStore
- Add selectable/selected props to TransactionCard with checkbox
- Add SettlementHistory component with expandable transactions
- Add trash view with restore and permanent delete buttons
- Add bulk selection toolbar with 'Zelfde personen' and 'Verwijderen'
- Add bulk splits modal for applying same splits to multiple transactions
- Add toast notifications for user feedback

Resolves: APP-18
```
