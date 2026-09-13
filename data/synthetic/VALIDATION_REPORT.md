# SARVSAKSHI synthetic enrichment validation

This report is for the SYNTHETIC HYBRID prototype layer. It is not a government dataset.

- ok: `True`
- total synthetic records: **10000**
- unique real internal_project_id values: **10000**
- unique synthetic_record_id values: **10000**
- duplicate synthetic IDs: **0**

## Scenario distribution

- `COST_ANOMALY`: 999 (9.99%)
- `DEMO_CLEAN`: 1 (0.01%)
- `DEMO_GHOST`: 1 (0.01%)
- `DEMO_OVERBILL`: 1 (0.01%)
- `DEMO_STUCK`: 1 (0.01%)
- `EVIDENCE_GHOST`: 399 (3.99%)
- `MIXED`: 300 (3.00%)
- `NORMAL`: 6999 (69.99%)
- `OVERLAP`: 500 (5.00%)
- `TIME_ANOMALY`: 799 (7.99%)

## Controlled demo cases

- `GHOST`: `internal:464569d6e0e8fa677cd826b350df9c2c0bd680a7665587cadd63e93e2b357d29`
- `OVERBILL`: `internal:eab396eafd121f6c8426cb285be2078aa7cfc6fe718050d6eb7340208318e762`
- `STUCK`: `internal:639b82094c0b023fa8fd1047f88e87a608a92f59442a74bf086ab25d4a2274c5`
- `CLEAN`: `internal:e714d635eb46ac65589489b3972d8cf896f9c2b7baaaeb753bf3e312929fc3b9`

## Missing values

- `demo_case_id`: 9996 (99.96%)
- `mixed_signals`: 9700 (97.00%)
- `overlap_group_id`: 9400 (94.00%)
- `anomaly_notes`: 6999 (69.99%)
- `real_constituency`: 1 (0.01%)
- `real_status`: 199 (1.99%)
- `real_city`: 7806 (78.06%)
- `real_block`: 2434 (24.34%)
- `real_village`: 2434 (24.34%)
- `sanction_date`: 5368 (53.68%)
- `planned_start_date`: 5368 (53.68%)
- `planned_completion_date`: 5368 (53.68%)
- `actual_start_date`: 7124 (71.24%)
- `actual_completion_date`: 8433 (84.33%)
- `sanctioned_amount`: 5368 (53.68%)
- `expenditure_amount`: 5368 (53.68%)
- `latitude`: 213 (2.13%)
- `longitude`: 213 (2.13%)
- `milestone_number`: 7165 (71.65%)
- `milestone_amount`: 7165 (71.65%)
- `milestone_total_amount`: 7165 (71.65%)

## Hard constraint violations (generator bugs)

- none

## Intended prototype anomaly signals (not generator bugs)

- `expenditure_gt_sanctioned`: 1300
- `ghost_implausible_gps`: 287
- `ghost_missing_gps`: 213
- `milestone_total_gt_sanctioned`: 1300
- `time_anomaly_rows`: 900

## Sample REAL + SYNTHETIC/HYBRID records

### Sample 1: `DEMO_CLEAN`

```
{
  "synthetic_record_id": "synthetic:enr:26102:008997",
  "internal_project_id": "internal:e714d635eb46ac65589489b3972d8cf896f9c2b7baaaeb753bf3e312929fc3b9",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "DEMO_CLEAN",
  "demo_case_id": "CLEAN",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "KADAPA",
  "real_status": "Sanctioned",
  "real_allocation_amount": "3500000",
  "real_recommended_date": "2023-10-30",
  "implementing_district": "CUDDAPAH [SYNTHETIC]",
  "vendor_name": "SYNTHETIC CUDDAPAH Roadworks Agency",
  "sanction_date": "2023-11-16",
  "planned_start_date": "2024-06-23",
  "planned_completion_date": "2024-12-24",
  "actual_start_date": "",
  "actual_completion_date": "",
  "sanctioned_amount": "3500000",
  "expenditure_amount": "0",
  "latitude": "14.451364",
  "longitude": "78.831066",
  "physical_progress_percent": "0",
  "milestone_number": "",
  "milestone_amount": "",
  "milestone_total_amount": "",
  "anomaly_notes": "DEMO_CLEAN: internally consistent SYNTHETIC enrichment for the prototype clean case."
}
```

### Sample 2: `DEMO_OVERBILL`

```
{
  "synthetic_record_id": "synthetic:enr:26102:009140",
  "internal_project_id": "internal:eab396eafd121f6c8426cb285be2078aa7cfc6fe718050d6eb7340208318e762",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "DEMO_OVERBILL",
  "demo_case_id": "OVERBILL",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "ELURU",
  "real_status": "Completed",
  "real_allocation_amount": "3550000",
  "real_recommended_date": "2023-11-21",
  "implementing_district": "ELURU [SYNTHETIC]",
  "vendor_name": "SYNTHETIC ELURU Water Systems Agency",
  "sanction_date": "2023-12-06",
  "planned_start_date": "2023-12-24",
  "planned_completion_date": "2024-08-29",
  "actual_start_date": "2023-12-28",
  "actual_completion_date": "2024-06-30",
  "sanctioned_amount": "3550000",
  "expenditure_amount": "6390000",
  "latitude": "16.766328",
  "longitude": "81.154918",
  "physical_progress_percent": "100",
  "milestone_number": "3",
  "milestone_amount": "1479166",
  "milestone_total_amount": "4437500",
  "anomaly_notes": "DEMO_OVERBILL: SYNTHETIC expenditure and milestone total exceed sanctioned amount. Prototype case only; not a legal finding."
}
```

### Sample 3: `DEMO_STUCK`

```
{
  "synthetic_record_id": "synthetic:enr:26102:003926",
  "internal_project_id": "internal:639b82094c0b023fa8fd1047f88e87a608a92f59442a74bf086ab25d4a2274c5",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "DEMO_STUCK",
  "demo_case_id": "STUCK",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "ANANTAPUR",
  "real_status": "Ongoing",
  "real_allocation_amount": "1000000",
  "real_recommended_date": "2023-07-16",
  "implementing_district": "ANANTAPUR [SYNTHETIC]",
  "vendor_name": "SYNTHETIC ANANTAPUR Community Works Constructions",
  "sanction_date": "2023-08-22",
  "planned_start_date": "2023-09-02",
  "planned_completion_date": "2024-04-11",
  "actual_start_date": "2023-09-02",
  "actual_completion_date": "",
  "sanctioned_amount": "1000000",
  "expenditure_amount": "108000",
  "latitude": "14.727152",
  "longitude": "77.603815",
  "physical_progress_percent": "12",
  "milestone_number": "1",
  "milestone_amount": "108000",
  "milestone_total_amount": "108000",
  "anomaly_notes": "DEMO_STUCK: SYNTHETIC overdue schedule with low physical progress and no completion date. Prototype case only; not a legal finding."
}
```

### Sample 4: `DEMO_GHOST`

```
{
  "synthetic_record_id": "synthetic:enr:26102:002764",
  "internal_project_id": "internal:464569d6e0e8fa677cd826b350df9c2c0bd680a7665587cadd63e93e2b357d29",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "DEMO_GHOST",
  "demo_case_id": "GHOST",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "VIZIANAGARAM",
  "real_status": "Completed",
  "real_allocation_amount": "7378000",
  "real_recommended_date": "2023-07-09",
  "implementing_district": "VIZIANAGARAM [SYNTHETIC]",
  "vendor_name": "SYNTHETIC VIZIANAGARAM General Works Agency",
  "sanction_date": "2023-07-17",
  "planned_start_date": "2023-08-02",
  "planned_completion_date": "2024-01-14",
  "actual_start_date": "2023-08-11",
  "actual_completion_date": "2024-01-20",
  "sanctioned_amount": "7378000",
  "expenditure_amount": "7242167",
  "latitude": "10.05",
  "longitude": "68.4",
  "physical_progress_percent": "100",
  "milestone_number": "4",
  "milestone_amount": "1810541",
  "milestone_total_amount": "7242167",
  "anomaly_notes": "DEMO_GHOST: SYNTHETIC completed claim with coordinates that do not match the real state/constituency. Prototype case only; not a legal finding."
}
```

### Sample 5: `NORMAL`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000003",
  "internal_project_id": "internal:000e764d2fd2fa32634d820007d2f7b6a5bba6b884ee1a14c63ec7548462e821",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "NORMAL",
  "demo_case_id": "",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "KURNOOL",
  "real_status": "",
  "real_allocation_amount": "63577",
  "real_recommended_date": "2023-08-24",
  "implementing_district": "KURNOOL [SYNTHETIC]",
  "vendor_name": "SYNTHETIC KURNOOL Roadworks Contractor",
  "sanction_date": "",
  "planned_start_date": "",
  "planned_completion_date": "",
  "actual_start_date": "",
  "actual_completion_date": "",
  "sanctioned_amount": "",
  "expenditure_amount": "",
  "latitude": "15.859961",
  "longitude": "78.058741",
  "physical_progress_percent": "0",
  "milestone_number": "",
  "milestone_amount": "",
  "milestone_total_amount": "",
  "anomaly_notes": ""
}
```

### Sample 6: `COST_ANOMALY`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000007",
  "internal_project_id": "internal:0033ace4dd4766a36eab8a48f1bdd26706ae42f97ac0533d0eebe2190e2fbaa8",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "COST_ANOMALY",
  "demo_case_id": "",
  "mixed_signals": "",
  "real_state": "Andhra Pradesh",
  "real_constituency": "ARAKU(ST)",
  "real_status": "Completed",
  "real_allocation_amount": "194840",
  "real_recommended_date": "2023-11-04",
  "implementing_district": "ALLURI SITHARAMARAJU [SYNTHETIC]",
  "vendor_name": "SYNTHETIC ALLURI SITHARAMARAJU General Works Constructions",
  "sanction_date": "2023-12-02",
  "planned_start_date": "2023-12-13",
  "planned_completion_date": "2024-03-28",
  "actual_start_date": "2023-12-21",
  "actual_completion_date": "2024-03-31",
  "sanctioned_amount": "194840",
  "expenditure_amount": "401258",
  "latitude": "18.361462",
  "longitude": "82.888508",
  "physical_progress_percent": "100",
  "milestone_number": "4",
  "milestone_amount": "56783",
  "milestone_total_amount": "227134",
  "anomaly_notes": "SYNTHETIC COST_ANOMALY/OVERBILL signal for prototype testing; not a legal finding."
}
```

### Sample 7: `TIME_ANOMALY`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000002",
  "internal_project_id": "internal:000bb3edb94421c0949556be5dfa0210dd271e5974e274058d314ac25adad59a",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "TIME_ANOMALY",
  "demo_case_id": "",
  "mixed_signals": "",
  "real_state": "Madhya Pradesh",
  "real_constituency": "KHARGONE(ST)",
  "real_status": "Sanctioned",
  "real_allocation_amount": "300000",
  "real_recommended_date": "2023-08-06",
  "implementing_district": "BADWANI [SYNTHETIC]",
  "vendor_name": "SYNTHETIC BADWANI Community Works Contractor",
  "sanction_date": "2023-09-01",
  "planned_start_date": "2023-09-10",
  "planned_completion_date": "2024-05-01",
  "actual_start_date": "2023-09-10",
  "actual_completion_date": "",
  "sanctioned_amount": "300000",
  "expenditure_amount": "35100",
  "latitude": "22.687597",
  "longitude": "78.928191",
  "physical_progress_percent": "13",
  "milestone_number": "",
  "milestone_amount": "",
  "milestone_total_amount": "",
  "anomaly_notes": "SYNTHETIC TIME_ANOMALY/STUCK signal for prototype testing; not a legal finding."
}
```

### Sample 8: `OVERLAP`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000009",
  "internal_project_id": "internal:004e3c136b86a9af645706eb751dff19c13952cd5eeb24bdc923524fad78e5da",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "OVERLAP",
  "demo_case_id": "",
  "mixed_signals": "",
  "real_state": "Jammu And Kashmir",
  "real_constituency": "ANANTNAG",
  "real_status": "Unsanctioned",
  "real_allocation_amount": "591000",
  "real_recommended_date": "2023-11-16",
  "implementing_district": "ANANTNAG [SYNTHETIC]",
  "vendor_name": "SYNTHETIC ANANTNAG General Works Agency",
  "sanction_date": "",
  "planned_start_date": "",
  "planned_completion_date": "",
  "actual_start_date": "",
  "actual_completion_date": "",
  "sanctioned_amount": "",
  "expenditure_amount": "",
  "latitude": "33.6215",
  "longitude": "75.230535",
  "physical_progress_percent": "0",
  "milestone_number": "",
  "milestone_amount": "",
  "milestone_total_amount": "",
  "anomaly_notes": "SYNTHETIC OVERLAP group: nearby coordinates and shared vendor for prototype testing; not a legal finding."
}
```

### Sample 9: `EVIDENCE_GHOST`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000001",
  "internal_project_id": "internal:000ae0add6210c0af931a8b36e624b2bf321ab28d25f309b270d306551c499f9",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "EVIDENCE_GHOST",
  "demo_case_id": "",
  "mixed_signals": "",
  "real_state": "Tamil Nadu",
  "real_constituency": "VILUPPURAM(SC)",
  "real_status": "Completed",
  "real_allocation_amount": "1400000",
  "real_recommended_date": "2023-08-18",
  "implementing_district": "VILLUPURAM [SYNTHETIC]",
  "vendor_name": "SYNTHETIC VILLUPURAM Building Works Constructions",
  "sanction_date": "2023-09-05",
  "planned_start_date": "2023-09-22",
  "planned_completion_date": "2024-03-30",
  "actual_start_date": "2023-09-24",
  "actual_completion_date": "2024-03-23",
  "sanctioned_amount": "1400000",
  "expenditure_amount": "1330295",
  "latitude": "",
  "longitude": "",
  "physical_progress_percent": "100",
  "milestone_number": "2",
  "milestone_amount": "665147",
  "milestone_total_amount": "1330295",
  "anomaly_notes": "SYNTHETIC EVIDENCE/GHOST: completed claim with no coordinates."
}
```

### Sample 10: `MIXED`

```
{
  "synthetic_record_id": "synthetic:enr:26102:000013",
  "internal_project_id": "internal:006129520766829b3c49e80e1c687e382a58ca187a36c35df11612b5dbd2e991",
  "record_mode": "HYBRID",
  "enrichment_source": "SYNTHETIC",
  "scenario_type": "MIXED",
  "demo_case_id": "",
  "mixed_signals": "COST_ANOMALY,TIME_ANOMALY",
  "real_state": "Tamil Nadu",
  "real_constituency": "CUDDALORE",
  "real_status": "Completed",
  "real_allocation_amount": "450000",
  "real_recommended_date": "2023-12-20",
  "implementing_district": "CUDDALORE [SYNTHETIC]",
  "vendor_name": "SYNTHETIC CUDDALORE Lighting Works Constructions",
  "sanction_date": "2024-01-26",
  "planned_start_date": "2024-02-04",
  "planned_completion_date": "2024-04-22",
  "actual_start_date": "2024-02-04",
  "actual_completion_date": "2024-08-22",
  "sanctioned_amount": "450000",
  "expenditure_amount": "655988",
  "latitude": "10.811845",
  "longitude": "78.868247",
  "physical_progress_percent": "100",
  "milestone_number": "4",
  "milestone_amount": "160772",
  "milestone_total_amount": "643091",
  "anomaly_notes": "SYNTHETIC TIME_ANOMALY/STUCK signal for prototype testing; not a legal finding. | SYNTHETIC COST_ANOMALY/OVERBILL signal for prototype testing; not a legal finding. | SYNTHETIC MIXED signals: COST_ANOMALY,TIME_ANOMALY"
}
```

