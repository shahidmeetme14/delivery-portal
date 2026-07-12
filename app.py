if st.button("🔍 Fetch Live Status from PakPost Server", use_container_width=True):
                        with st.spinner("Connecting to EMTTS Logistics Data Pipeline..."):
                            data, err = fetch_live_emtts_status(target_profile['article_id'])
                            
                            if err:
                                st.error(err)
                            elif data and data["history"]:
                                history_list = data["history"]
                                last_entry = history_list[-1]
                                last_status_lower = last_entry["status"].lower()
                                
                                # --- LOGIC ENGINE ---
                                # 1. Check for Historical Anomaly (Delivered/RTS in the middle)
                                is_historical_anomaly = False
                                for entry in history_list[:-1]: # Sub-list except last
                                    s = entry["status"].lower()
                                    if "delivered" in s or "return" in s or "rts" in s:
                                        is_historical_anomaly = True
                                        break
                                
                                # 2. Determine Final Status State
                                is_last_delivered = "delivered" in last_status_lower
                                is_last_rts = "return" in last_status_lower or "rts" in last_status_lower
                                
                                # --- UI RENDERING ---
                                
                                # Blinking Alert (Only if history had it, but final doesn't)
                                if is_historical_anomaly and not (is_last_delivered or is_last_rts):
                                    st.markdown("""
                                        <style>
                                        @keyframes criticalBlink { 0% { background-color: #dc2626; color: white; } 50% { background-color: #fee2e2; color: #b91c1c; } 100% { background-color: #dc2626; color: white; } }
                                        .emtts-blink-container { animation: criticalBlink 1.2s infinite; padding: 14px; border-radius: 6px; font-weight: 800; text-align: center; border: 2px solid #b91c1c; margin-bottom: 15px; }
                                        </style>
                                        <div class="emtts-blink-container">⚠️ ANOMALY DETECTED: This article was previously marked as Delivered/RTS in history but is NOT currently in that state!</div>
                                    """, unsafe_allow_html=True)
                                
                                # Final Status Highlights
                                if is_last_delivered:
                                    st.success(f"✅ FINAL STATUS: {last_entry['status']} (Date: {last_entry['datetime']})")
                                elif is_last_rts:
                                    st.error(f"❌ FINAL STATUS: {last_entry['status']} (Date: {last_entry['datetime']})")
                                else:
                                    st.info(f"📍 CURRENT STATUS: {last_entry['status']} (Last Office: {last_entry['office']})")

                                # Data Display Mode
                                use_mapped = (data_mode == "Fetch Snipped Data (Mapped Mode)")
                                
                                if report_scope == "All Statuses (Full History)":
                                    processed_rows = []
                                    for idx, h in enumerate(history_list):
                                        processed_rows.append({
                                            "Event": idx + 1,
                                            "Time": h["datetime"],
                                            "Office": h["office"],
                                            "Status": map_status(h["status"]) if use_mapped else h["status"]
                                        })
                                    st.dataframe(pd.DataFrame(processed_rows), use_container_width=True)
                            else:
                                st.warning("Tracking frame executed successfully but data arrays remain empty.")
