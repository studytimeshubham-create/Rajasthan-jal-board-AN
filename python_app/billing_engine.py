import math
from datetime import date

def calculate_bill(
    consumption_kl: float,
    consumer: dict,
    rates: dict,
    previous_outstanding: float = 0.0,
    credit_balance: float = 0.0,
    last_payment_date: date = None,
    payment_date: date = None,
    avg_6month_kl: float = None
) -> dict:
    """Calculates water bill breakdown dynamically using charges config rates."""
    category = consumer.get("category", "Domestic")
    meter_size = consumer.get("meter_size", "15mm")
    status = consumer.get("consumer_status", "Active")
    flat_rate_attr = consumer.get("custom_attributes", {}).get("is_flat_rate_rural", False)
    is_flat_rate_rural = str(flat_rate_attr).lower() == "true" or bool(consumer.get("is_flat_rate_rural", False))
    
    # 1. Determine size type (15-25mm standard vs bulk >25mm)
    is_bulk = meter_size not in ["15mm", "20mm", "25mm"]
    
    # 2. Water charge & slabs calculation
    water_charge = 0.0
    slab_details = []
    min_charge_applied = False
    min_charge_amount = 0.0
    
    # Check special domestic waiver: 15mm, active/functional meter, and consumption <= 15 KL
    is_domestic_15mm_waiver = (
        category == "Domestic" and 
        meter_size == "15mm" and 
        status == "Active" and 
        consumption_kl <= 15.0 and
        not is_flat_rate_rural
    )
    
    if is_flat_rate_rural and category == "Domestic" and meter_size == "15mm":
        # Flat Rate Rural Domestic
        water_charge = float(rates.get("domestic_flat_rural", 110.0))
        slab_details.append({
            "slab": "Flat Rate Rural",
            "kl": consumption_kl,
            "rate": water_charge,
            "amount": water_charge
        })
    elif is_domestic_15mm_waiver:
        # Domestic waiver applies
        water_charge = 0.0
        slab_details.append({
            "slab": "Domestic Waiver (<=15 KL)",
            "kl": consumption_kl,
            "rate": 0.0,
            "amount": 0.0
        })
    elif is_bulk:
        # Bulk connections (>25mm)
        rate_key = f"bulk_{category.lower().replace('-', '')}_rate"
        bulk_rate = float(rates.get(rate_key, 25.0 if category == "Domestic" else (97.0 if category == "Non-Domestic" else 220.0)))
        water_charge = consumption_kl * bulk_rate
        
        slab_details.append({
            "slab": f"Bulk {category}",
            "kl": consumption_kl,
            "rate": bulk_rate,
            "amount": water_charge
        })
        
        # Apply bulk minimum monthly charges
        cat_key = "dom" if category == "Domestic" else ("nondom" if category == "Non-Domestic" else "ind")
        min_key = f"bulk_min_{cat_key}_{meter_size}"
        min_charge_amount = float(rates.get(min_key, 0.0))
        if water_charge < min_charge_amount:
            water_charge = min_charge_amount
            min_charge_applied = True
            
    else:
        # Standard connections (15mm - 25mm) slab calculation
        slab_details = get_slab_breakdown(consumption_kl, category, meter_size, rates)
        water_charge = sum(s["amount"] for s in slab_details)
        
        # Apply standard minimum monthly charges
        # Minimum charges apply only if consumption > 15 KL for Domestic
        if category == "Domestic":
            if consumption_kl > 15.0:
                if meter_size == "15mm":
                    # Check avg_6month_kl or current consumption
                    avg_check = avg_6month_kl if avg_6month_kl is not None else consumption_kl
                    if avg_check <= 8.0:
                        min_charge_amount = float(rates.get("domestic_min_15mm_avg_low", 88.0))
                    else:
                        min_charge_amount = float(rates.get("domestic_min_15mm_avg_high", 220.0))
                elif meter_size == "20mm":
                    min_charge_amount = float(rates.get("domestic_min_20mm", 880.0))
                elif meter_size == "25mm":
                    min_charge_amount = float(rates.get("domestic_min_25mm", 2200.0))
                
                if water_charge < min_charge_amount:
                    water_charge = min_charge_amount
                    min_charge_applied = True
        else:
            # Non-Domestic / Industrial always has minimum monthly charges
            cat_pref = "nondomestic" if category == "Non-Domestic" else "industrial"
            min_key = f"{cat_pref}_min_{meter_size}"
            min_charge_amount = float(rates.get(min_key, 0.0))
            if water_charge < min_charge_amount:
                water_charge = min_charge_amount
                min_charge_applied = True

    # 3. Fixed Charge (Capital Renovation)
    fixed_charge = 0.0
    if is_flat_rate_rural and category == "Domestic" and meter_size == "15mm":
        # Fixed charge not applicable on flat rate rural connections
        fixed_charge = 0.0
    elif is_bulk:
        cat_key = "dom" if category == "Domestic" else ("nondom" if category == "Non-Domestic" else "ind")
        fixed_key = f"bulk_fixed_{cat_key}_{meter_size}"
        fixed_charge = float(rates.get(fixed_key, 0.0))
    else:
        fixed_key = f"fixed_charge_{category.lower().replace('-', '')}"
        fixed_charge = float(rates.get(fixed_key, 0.0))
        
    # 4. Meter Service Charge
    meter_service_charge = 0.0
    if is_bulk:
        svc_key = f"bulk_svc_{meter_size}"
        meter_service_charge = float(rates.get(svc_key, 0.0))
    else:
        svc_key = f"meter_svc_{meter_size}"
        meter_service_charge = float(rates.get(svc_key, 0.0))

    # 5. Infrastructure Development Surcharge (IDS)
    # Up to 15 KL: No IDS
    # 15.001 - 40 KL: 25% of total monthly charges
    # Above 40 KL: 35% of total monthly charges
    # Total monthly charges = water_charge + fixed_charge + meter_service_charge
    ids_rate_pct = 0.0
    if consumption_kl > 15.0 and consumption_kl <= 40.0:
        ids_rate_pct = 25.0
    elif consumption_kl > 40.0:
        ids_rate_pct = 35.0
        
    monthly_subtotal = water_charge + fixed_charge + meter_service_charge
    ids_charge = round((ids_rate_pct / 100.0) * monthly_subtotal, 2)
    
    # 5.1 Sewerage Tax (Clause 14)
    # Sewerage Tax only applies if water charges are chargeable (water_charge > 0)
    # OR if it's Own/Mixed supply (as per Clause 14 Mixed is treated as Own)
    sewerage_tax = 0.0
    has_sewerage = bool(consumer.get("has_sewerage", False))
    supply_type = consumer.get("supply_type", "PHED")
    sub_category = consumer.get("sewerage_sub_category")

    if has_sewerage:
        # Clause 14 Note: If water charges are not chargeable, Sewerage Tax will also not be chargeable.
        # This applies specifically to the Domestic 15mm <= 15 KL waiver.
        if is_domestic_15mm_waiver:
            sewerage_tax = 0.0
        elif supply_type == "PHED":
            # 20% of water charges
            if water_charge > 0:
                sewerage_tax = round(water_charge * (float(rates.get("sewerage_phed_supply_rate_pct", 20.0)) / 100.0), 2)
        else:
            # Own or Mixed Supply (Treated as Own)
            if sub_category == "Hotel":
                rooms = int(consumer.get("rooms_count", 0))
                sewerage_tax = rooms * float(rates.get("sewerage_own_hotel_per_room", 31.25))
            elif sub_category == "Restaurant":
                sewerage_tax = float(rates.get("sewerage_own_restaurant", 200.00))
            elif sub_category == "Cinema":
                sewerage_tax = float(rates.get("sewerage_own_cinema", 400.00))
            elif sub_category == "Car/Truck Service Station":
                sewerage_tax = float(rates.get("sewerage_own_car_service", 200.00))
            elif sub_category == "Scooter Service Station":
                sewerage_tax = float(rates.get("sewerage_own_scooter_service", 62.50))
            elif sub_category == "Other Industrial/Commercial":
                rooms = int(consumer.get("rooms_count", 0))
                sewerage_tax = rooms * float(rates.get("sewerage_own_other_ind_comm_per_room", 12.50))
            elif sub_category == "Domestic":
                sewerage_tax = float(rates.get("sewerage_own_domestic", 12.50))
            elif sub_category == "House > 200sqm":
                area = float(consumer.get("plot_area_sqm", 0.0))
                sewerage_tax = (area / 100.0) * float(rates.get("sewerage_own_house_large_per_100sqm", 6.25))

    # 5.2 Sewerage Treatment Plant (STP) Charges (Clause 15)
    # 13% of water charges
    stp_charge = 0.0
    if bool(consumer.get("has_stp", False)):
        if water_charge > 0:
            stp_charge = round(water_charge * (float(rates.get("stp_charge_rate_pct", 13.0)) / 100.0), 2)

    monthly_subtotal = water_charge + fixed_charge + meter_service_charge + sewerage_tax + stp_charge
    ids_charge = round((ids_rate_pct / 100.0) * monthly_subtotal, 2)

    subtotal_before_lps = monthly_subtotal + ids_charge
    
    # 6. Apply credit balance to new monthly charges
    credit_applied = 0.0
    if credit_balance > 0:
        if credit_balance >= subtotal_before_lps:
            credit_applied = subtotal_before_lps
            remaining_credit = credit_balance - subtotal_before_lps
        else:
            credit_applied = credit_balance
            remaining_credit = 0.0
    else:
        remaining_credit = 0.0
        
    subtotal_after_credit = subtotal_before_lps - credit_applied
    
    # 7. Late Payment Surcharge (LPS)
    lps_amount = 0.0
    lps_type = "none"
    lps_applicable = False
    
    # LPS applies if payment date is set and is after last payment date, 
    # AND there is remaining unpaid subtotal (i.e. credit did not cover it).
    if last_payment_date and payment_date and subtotal_after_credit > 0:
        lps_res = apply_lps(subtotal_before_lps, last_payment_date, payment_date, credit_balance, previous_outstanding)
        lps_amount = lps_res["lps_amount"]
        lps_type = lps_res["lps_type"]
        lps_applicable = lps_res["lps_applicable"]
        
    # 8. Accumulate totals
    total_before_rounding = subtotal_after_credit + previous_outstanding + lps_amount
    total_amount = math.ceil(total_before_rounding)
    
    # 9. Anomaly detection
    is_anomaly = False
    if avg_6month_kl is not None and consumption_kl > (3 * avg_6month_kl):
        is_anomaly = True

    return {
        "water_charge": water_charge,
        "slab_details": slab_details,
        "minimum_charge_applied": min_charge_applied,
        "minimum_charge_amount": min_charge_amount,
        "fixed_charge": fixed_charge,
        "meter_service_charge": meter_service_charge,
        "sewerage_tax": sewerage_tax,
        "stp_charge": stp_charge,
        "ids_charge": ids_charge,
        "ids_rate_pct": ids_rate_pct,
        "previous_outstanding": previous_outstanding,
        "credit_applied": credit_applied,
        "remaining_credit": remaining_credit,
        "lps_amount": lps_amount,
        "lps_type": lps_type,
        "lps_applicable": lps_applicable,
        "subtotal_before_lps": subtotal_before_lps,
        "total_before_rounding": total_before_rounding,
        "total_amount": total_amount,
        "is_anomaly": is_anomaly,
        "is_flat_rate_rural": is_flat_rate_rural
    }

def get_slab_breakdown(consumption_kl: float, category: str, meter_size: str, rates: dict) -> list:
    """Calculates standard slab-by-slab water charges."""
    slab_details = []
    remaining = consumption_kl
    
    if category == "Domestic":
        # Slabs: 0-8 KL (rate 7), 8-15 KL (rate 9), 15-40 KL (rate 18), >40 KL (rate 22)
        slabs = [
            ("Slab 0-8 KL", 8.0, float(rates.get("domestic_slab_a_rate", 7.00))),
            ("Slab 8-15 KL", 7.0, float(rates.get("domestic_slab_b_rate", 9.00))),
            ("Slab 15-40 KL", 25.0, float(rates.get("domestic_slab_c_rate", 18.00))),
            ("Slab Above 40 KL", float("inf"), float(rates.get("domestic_slab_d_rate", 22.00)))
        ]
    elif category == "Non-Domestic":
        # Slabs: 0-15 KL (rate 40), 15-40 KL (rate 73), >40 KL (rate 97)
        slabs = [
            ("Slab 0-15 KL", 15.0, float(rates.get("nondomestic_slab_a_rate", 40.00))),
            ("Slab 15-40 KL", 25.0, float(rates.get("nondomestic_slab_b_rate", 73.00))),
            ("Slab Above 40 KL", float("inf"), float(rates.get("nondomestic_slab_c_rate", 97.00)))
        ]
    elif category == "Industrial":
        # Slabs: 0-15 (rate 154), 15-40 (rate 198), >40 (rate 220)
        slabs = [
            ("Slab 0-15 KL", 15.0, float(rates.get("industrial_slab_a_rate", 154.00))),
            ("Slab 15-40 KL", 25.0, float(rates.get("industrial_slab_b_rate", 198.00))),
            ("Slab Above 40 KL", float("inf"), float(rates.get("industrial_slab_c_rate", 220.00)))
        ]
    else:
        # Fallback to simple domestic
        slabs = [("Slab All", float("inf"), 10.00)]
        
    for name, limit, rate in slabs:
        if remaining <= 0:
            break
        chunk = min(remaining, limit)
        amount = chunk * rate
        slab_details.append({
            "slab": name,
            "kl": chunk,
            "rate": rate,
            "amount": round(amount, 2)
        })
        remaining -= chunk
        
    return slab_details

def apply_lps(bill_total: float, last_payment_date: date, payment_date: date, credit_balance: float, outstanding: float) -> dict:
    """Calculates Late Payment Surcharge (LPS) amount and type based on payment delay."""
    # Check if credit balance covers the full bill. If so, no LPS.
    if credit_balance >= bill_total:
        return {"lps_amount": 0.0, "lps_type": "none", "lps_applicable": False}
        
    if payment_date <= last_payment_date:
        return {"lps_amount": 0.0, "lps_type": "none", "lps_applicable": False}
        
    # Calculate difference in months / days
    from dateutil.relativedelta import relativedelta
    diff = relativedelta(payment_date, last_payment_date)
    months_diff = diff.years * 12 + diff.months
    
    # Subtotal to apply LPS rate to is the monthly bill total
    lps_base = bill_total
    
    # Check if delay is within 2 calendar months after the last_payment_date
    limit_2_months = last_payment_date + relativedelta(months=2)
    
    if payment_date <= limit_2_months:
        lps_amount = round(lps_base * 0.10, 2)
        return {"lps_amount": lps_amount, "lps_type": "10pct", "lps_applicable": True}
    else:
        # Beyond 2 months: 10% LPS + 18% annual interest on outstanding (meaning the past outstanding balance being paid)
        lps_amount_10 = lps_base * 0.10
        
        # Interest is 18% annual on outstanding balance for the period of delay
        # Calculate exact days past due
        days_past_due = (payment_date - last_payment_date).days
        interest = outstanding * 0.18 * (days_past_due / 365.0)
        
        total_lps = round(lps_amount_10 + interest, 2)
        return {"lps_amount": total_lps, "lps_type": "10pct_plus_interest", "lps_applicable": True}
