def troubleshoot(request):
    """Expose the hunter-email-sinkhole state to every template so base.html
    can show a persistent warning banner while it's active."""
    from dashboards.models import TroubleshootSettings
    row = TroubleshootSettings.objects.filter(settings_id=1).first()
    return {
        "hunter_email_sinkhole_active": bool(row and row.hunter_email_sinkhole),
        "sinkhole_enabled_by": row.sinkhole_enabled_by if row else "",
        "sinkhole_enabled_at": row.sinkhole_enabled_at if row else None,
    }
