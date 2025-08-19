get_users_q = '{"query": "{ users { name user_id, email ,integrations } }"}'
get_meeting_details_q = '{"query": "query Transcript($transcriptId: String!) { transcript(id: $transcriptId) { title id calendar_id date duration host_email transcript_url audio_url video_url participants  meeting_attendees { email } calendar_id summary { action_items keywords outline overview shorthand_bullet }  }  }", "variables": {"transcriptId": "__tid__"}}'
synced_events_q = "SELECT transcript_id FROM `kitrum-cloud.logging.crm_fireflies_integration` where status in ('success', 'partial success')"
delete_logs_q = "DELETE FROM `kitrum-cloud.logging.crm_fireflies_integration` where transcript_id = '<tid>'"

