# Lima Construction Source Findings

## Purpose
This document captures the first approved Lima construction-oriented sources for the raw-ingestion Lambda.

The goal is not to claim full Lima Metropolitana coverage yet. The goal is to start from trusted, direct resource URLs that already expose permit and construction-completion signals.

## Summary
The first 3 approved sources for Lambda testing are:

1. Municipalidad Metropolitana de Lima `Resoluciones de Licencias de Edificación`
2. Municipalidad Metropolitana de Lima `Conformidad de Obra y Declaratoria de Edificación`
3. Municipalidad de San Isidro `Licencias de Edificación`

These are better primary ingestion targets than the SAT `Predios del Cercado de Lima` series because they track administrative construction activity directly instead of property stock and valuation.

## Why These Sources Were Chosen

### 1. MML `Resoluciones de Licencias de Edificación`
- Dataset page: `https://www.datosabiertos.gob.pe/dataset/resoluciones-de-licencias-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima`
- Direct resource URL: `https://www.datosabiertos.gob.pe/sites/default/files/DATASET%20RESOLUCION%20DE%20LICENCIAS%20DE%20EDIFICACION%20MOD%20A%2CB%2CC%2CD.csv`
- Scope: `Cercado de Lima`
- Last modified on portal: `2024-01-31`

Why it matters:
- It measures permit issuance directly.
- It includes issuance dates, expediente numbers, type of use, zoning, and height.
- It is a good first permit-flow dataset for Lima.

Observed schema sample:
- `FECHA DE EMISION DE LICENCIA`
- `N° EXPEDIENTE`
- `N° RESOLUCION DE LICENCIA`
- `TIPO DE USO`
- `NOMBRE DE VIA`
- `CODIGO CATASTRAL`
- `ZONIFICACION`
- `ALTURA`

Known ingestion caveats:
- CSV contains blank rows between data rows.
- Encoding and delimiter cleanup will be needed downstream.

### 2. MML `Conformidad de Obra y Declaratoria de Edificación`
- Dataset page: `https://www.datosabiertos.gob.pe/dataset/conformidad-de-obra-y-declaratoria-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima`
- Direct resource URL: `https://www.datosabiertos.gob.pe/sites/default/files/DATASET%20CONFORMIDAD%20Y%20DECLARATORIA%20DE%20FABRICA%20EMITIDOS%20050125.csv`
- Scope: `Cercado de Lima`
- Last modified on portal: `2024-01-31`

Why it matters:
- It complements the permit dataset with a downstream completion or formalization signal.
- It supports a pipeline view: permit issuance versus completed or regularized works.
- It includes use, type, address, zoning, approval modality, and value fields.

Observed schema sample:
- `FECHA_DE_EMISION`
- `DIRECCION`
- `MODALIDAD_DE_APROBACION`
- `TIPO`
- `USO`
- `VALORIZACION_DE_LA_OBRA`
- `DERECHO_DE_TRAMITE`

Known ingestion caveats:
- CSV also contains blank rows between data rows.
- This is not the same stage as permit issuance, so analysis should keep it as a separate signal.

### 3. San Isidro `Licencias de Edificación`
- Dataset page: `https://www.datosabiertos.gob.pe/dataset/mdsi-licencias-de-edificacion-autorizacion-y-control`
- Direct resource URL: `https://www.datosabiertos.gob.pe/sites/default/files/licencias_de_edificacion.csv`
- Complementary resource URL: `https://www.datosabiertos.gob.pe/sites/default/files/conformidad_de_obra.csv`
- Scope: `San Isidro`
- Last modified on portal: `2025-10-23`

Why it matters:
- This is the richest source structurally among the first shortlist.
- It includes building use, work type, floors, units, areas, zoning, cadastral code, and coordinates.
- It works well as a district-level trend series and as a comparison point against MML.

Observed schema sample:
- `FECHA DE EMISION DE RESOLUCION`
- `N° DE RESOLUCION`
- `N° DE EXP.`
- `UBICACIÓN`
- `Urbanización`
- `ZONIFICACION`
- `TIPO DE EDIFICACION`
- `Numero de Pisos`
- `Numero de Unidades Inmobiliarias`
- `OBRA NUEVA Area (M2)`
- `AMPLIACION Area (M2)`
- `LATITUD`
- `LONGITUD`

Known ingestion caveats:
- CSV uses semicolon separators.
- Encoding cleanup will be needed downstream.
- This is district-level Lima, not metropolitan coverage.

## Sources Reviewed But Not Chosen First

### SAT `Predios del Cercado de Lima`
Why not first:
- Good contextual property-stock data.
- Not a direct construction-permit or completion-flow source.
- Better as a secondary urban-property context table later.

### San Miguel `Licencia de Edificaciones`
Why not first:
- Good permit schema.
- Appears useful as an expansion source.
- Visible annual resources look older than the three approved first sources.

### Miraflores `Resolución de Licencia de Edificaciones`
Why not first:
- Strong domain fit.
- Published as many separate monthly XLSX files, which raises ingestion complexity for the MVP.
- Good candidate for a later expansion phase.

## Recommended Analysis Framing
The first analysis should be framed as:

- permit issuance trend in `Cercado de Lima`
- completion or formalization trend in `Cercado de Lima`
- district-level permit trend in `San Isidro`

This supports:
- monthly counts
- monthly area totals
- monthly project value
- work-type composition
- use-type composition
- permit-versus-completion comparison inside MML

## Approved IDs For Lambda Testing
These IDs are repo-owned identifiers, not portal-owned identifiers.

### Approved entry 1
- `source_id`: `peru-open-data`
- `dataset_id`: `mml-resoluciones-licencias-edificacion`
- `resource_id`: `cercado-lima-licencias-csv`

### Approved entry 2
- `source_id`: `peru-open-data`
- `dataset_id`: `mml-conformidad-obra-declaratoria-edificacion`
- `resource_id`: `cercado-lima-conformidad-csv`

### Approved entry 3
- `source_id`: `peru-open-data`
- `dataset_id`: `san-isidro-licencias-edificacion`
- `resource_id`: `san-isidro-licencias-csv`

## Mapping Rule To Lambda Events
Each approved source maps directly into the existing Lambda event contract:

```json
{
  "source_id": "peru-open-data",
  "dataset_id": "mml-resoluciones-licencias-edificacion",
  "resource_id": "cercado-lima-licencias-csv",
  "ingestion_id": "2026-04-04T12:00:00Z",
  "request": {
    "kind": "url",
    "url": "https://www.datosabiertos.gob.pe/sites/default/files/DATASET%20RESOLUCION%20DE%20LICENCIAS%20DE%20EDIFICACION%20MOD%20A%2CB%2CC%2CD.csv",
    "method": "GET",
    "headers": {
      "Referer": "https://www.datosabiertos.gob.pe/dataset/resoluciones-de-licencias-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima"
    }
  }
}
```

The same rule applies to the other approved sources by changing only:
- `dataset_id`
- `resource_id`
- `request.url`
- `request.headers.Referer`
- optional metadata

## Next Recommended Step
Use the three event payloads in `infra/events/` to validate raw Lambda ingestion end to end before building any transformation logic.
