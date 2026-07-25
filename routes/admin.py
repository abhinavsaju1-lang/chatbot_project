from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, Response
import csv
import io
from database.mongodb import get_all_users, get_all_reports, delete_report, get_high_risk_users

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET'])
def admin():
    user_email = session.get('user_email')
    if not user_email:
        flash('Please login to access the Admin Panel.', 'warning')
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '').strip().lower()

    users = get_all_users()
    reports = get_all_reports()
    high_risk_users = get_high_risk_users()

    if not users:
        users = [
            {'name': 'Abhinav Saju', 'email': 'abhinav@mindsense.ai', 'is_admin': True, 'created_at': '2026-07-25'},
            {'name': 'Jane Doe', 'email': 'jane.doe@example.com', 'is_admin': False, 'created_at': '2026-07-25'},
            {'name': 'Data Science Student', 'email': 'student@mindsense.ai', 'is_admin': False, 'created_at': '2026-07-25'}
        ]

    if not reports:
        reports = [
            {
                'session_id': 'rep_m1',
                'report_type': 'mental',
                'title': 'Mental State Assessment Report',
                'patient_name': 'Jane Doe',
                'patient_email': 'jane.doe@example.com',
                'date': 'July 25, 2026',
                'risk_level': 'High Risk',
                'risk_badge': 'bg-rose-500 text-white',
                'scores': {'stress': 82, 'anxiety': 65, 'overall': 75}
            },
            {
                'session_id': 'rep_r1',
                'report_type': 'divorce',
                'title': 'Divorce Counseling Summary Report',
                'patient_name': 'Client Partner',
                'patient_email': 'partner@mindsense.ai',
                'date': 'July 25, 2026',
                'conflict_intensity': 'High Conflict Friction',
                'risk_badge': 'bg-rose-500 text-white',
                'scores': {'stress': 75, 'anxiety': 60, 'overall': 65}
            },
            {
                'session_id': 'rep_iq1',
                'report_type': 'iq',
                'title': 'IQ & Cognitive Assessment Report',
                'patient_name': 'Abhinav Saju',
                'patient_email': 'abhinav@mindsense.ai',
                'date': 'July 25, 2026',
                'cognitive_tier': 'Superior Cognitive Performance',
                'risk_badge': 'bg-amber-500 text-white',
                'estimated_iq_score': 125,
                'scores': {'stress': 15, 'anxiety': 10, 'overall': 20}
            }
        ]

    if search_query:
        users = [u for u in users if search_query in u.get('name', '').lower() or search_query in u.get('email', '').lower()]
        reports = [r for r in reports if search_query in r.get('patient_name', '').lower() or search_query in r.get('patient_email', '').lower()]
        high_risk_users = [h for h in high_risk_users if search_query in h.get('patient_name', '').lower() or search_query in h.get('patient_email', '').lower()]

    return render_template('admin.html', users=users, reports=reports, high_risk_users=high_risk_users, search_query=search_query)

@admin_bp.route('/admin/export-csv', methods=['GET'])
def export_csv():
    """Export system metrics, users, and reports into a CSV file download."""
    users = get_all_users()
    reports = get_all_reports()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write Header & User Data
    writer.writerow(['--- REGISTERED USERS ---'])
    writer.writerow(['Name', 'Email', 'Role', 'Account Created'])
    for u in users:
        writer.writerow([u.get('name'), u.get('email'), 'Admin' if u.get('is_admin') else 'User', u.get('created_at', '2026-07-25')])

    writer.writerow([])
    writer.writerow(['--- ASSESSMENT REPORTS ---'])
    writer.writerow(['Report Title', 'Patient Name', 'Patient Email', 'Date', 'Type'])
    for r in reports:
        writer.writerow([r.get('title'), r.get('patient_name'), r.get('patient_email'), r.get('date'), r.get('report_type')])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=mindsense_system_export.csv"}
    )

@admin_bp.route('/api/admin/delete-report', methods=['POST'])
def delete_report_api():
    data = request.get_json() or {}
    report_id = data.get('report_id')
    report_type = data.get('report_type', 'mental')

    if not report_id:
        return jsonify({'success': False, 'error': 'Report ID required'}), 400

    delete_report(report_id, report_type)
    return jsonify({'success': True, 'message': 'Report deleted successfully.'})
