from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize, serialize_list

time_bp = Blueprint('time_tracking', __name__, url_prefix='/api/time-tracking')


# ════════════════════════════════════════════════════════════════
# TIME TRACKING
# ════════════════════════════════════════════════════════════════

@time_bp.route('/start', methods=['POST'])
@jwt_required()
def start_timer():
    """Start a new time tracking session"""
    user_id = get_jwt_identity()
    data = request.get_json()
    project_id = data.get('project_id')
    description = data.get('description', '')
    
    if not project_id:
        return jsonify({'error': 'Project ID is required'}), 400
    
    # Verify project exists and user is the freelancer
    project = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if str(project.get('freelancer_id')) != user_id:
        return jsonify({'error': 'Only the freelancer can track time'}), 403
    
    # Check if timer already running
    active = mongo.db.time_entries.find_one({
        'freelancer_id': ObjectId(user_id),
        'project_id': ObjectId(project_id),
        'end_time': None
    })
    
    if active:
        return jsonify({'error': 'Timer already running for this project'}), 400
    
    # Create new time entry
    entry = {
        'project_id': ObjectId(project_id),
        'freelancer_id': ObjectId(user_id),
        'start_time': datetime.datetime.now(datetime.timezone.utc),
        'end_time': None,
        'description': description,
        'duration_seconds': 0,
        'created_at': datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.time_entries.insert_one(entry)
    entry['_id'] = result.inserted_id
    
    return jsonify({
        'message': 'Timer started',
        'timer': serialize(entry)
    }), 201


@time_bp.route('/stop/<timer_id>', methods=['POST'])
@jwt_required()
def stop_timer(timer_id):
    """Stop an active timer"""
    user_id = get_jwt_identity()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(timer_id)})
    except:
        return jsonify({'error': 'Invalid timer ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Timer not found'}), 404
    
    if str(entry['freelancer_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if entry.get('end_time'):
        return jsonify({'error': 'Timer already stopped'}), 400
    
    # Calculate duration
    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration_seconds = int((end_time - entry['start_time']).total_seconds())
    
    # Update entry
    mongo.db.time_entries.update_one(
        {'_id': ObjectId(timer_id)},
        {
            '$set': {
                'end_time': end_time,
                'duration_seconds': duration_seconds
            }
        }
    )
    
    return jsonify({
        'message': 'Timer stopped',
        'duration_seconds': duration_seconds,
        'duration_hours': round(duration_seconds / 3600, 2)
    }), 200


@time_bp.route('/pause/<timer_id>', methods=['POST'])
@jwt_required()
def pause_timer(timer_id):
    """Pause an active timer (useful for later resuming)"""
    user_id = get_jwt_identity()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(timer_id)})
    except:
        return jsonify({'error': 'Invalid timer ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Timer not found'}), 404
    
    if str(entry['freelancer_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if entry.get('paused_at'):
        return jsonify({'message': 'Timer already paused'}), 200
    
    mongo.db.time_entries.update_one(
        {'_id': ObjectId(timer_id)},
        {'$set': {'paused_at': datetime.datetime.now(datetime.timezone.utc)}}
    )
    
    return jsonify({'message': 'Timer paused'}), 200


@time_bp.route('/resume/<timer_id>', methods=['POST'])
@jwt_required()
def resume_timer(timer_id):
    """Resume a paused timer"""
    user_id = get_jwt_identity()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(timer_id)})
    except:
        return jsonify({'error': 'Invalid timer ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Timer not found'}), 404
    
    if str(entry['freelancer_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not entry.get('paused_at'):
        return jsonify({'message': 'Timer is not paused'}), 200
    
    # Calculate paused duration and add to total
    paused_duration = (datetime.datetime.now(datetime.timezone.utc) - entry['paused_at']).total_seconds()
    new_start = entry['start_time'] + datetime.timedelta(seconds=paused_duration)
    
    mongo.db.time_entries.update_one(
        {'_id': ObjectId(timer_id)},
        {
            '$set': {
                'start_time': new_start,
                'paused_at': None
            }
        }
    )
    
    return jsonify({'message': 'Timer resumed'}), 200


@time_bp.route('/entries/<project_id>', methods=['GET'])
@jwt_required()
def get_time_entries(project_id):
    """Get all time entries for a project"""
    user_id = get_jwt_identity()
    
    project = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Only client or freelancer can view
    if str(project.get('client_id')) != user_id and str(project.get('freelancer_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all entries for this project
    entries = list(mongo.db.time_entries.find(
        {'project_id': ObjectId(project_id)}
    ).sort('start_time', -1))
    
    total_seconds = sum(e.get('duration_seconds', 0) for e in entries)
    
    return jsonify({
        'entries': serialize_list(entries),
        'total_seconds': total_seconds,
        'total_hours': round(total_seconds / 3600, 2),
        'count': len(entries)
    }), 200


@time_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_my_time_entries():
    """Get all time entries for current freelancer"""
    user_id = get_jwt_identity()
    
    # Get date range if provided
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    project_id = request.args.get('project_id')
    
    query = {'freelancer_id': ObjectId(user_id)}
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            try:
                date_query['$gte'] = datetime.datetime.fromisoformat(start_date)
            except:
                pass
        if end_date:
            try:
                date_query['$lte'] = datetime.datetime.fromisoformat(end_date)
            except:
                pass
        if date_query:
            query['start_time'] = date_query
    
    if project_id:
        query['project_id'] = ObjectId(project_id)
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    total = mongo.db.time_entries.count_documents(query)
    entries = list(mongo.db.time_entries.find(query)
                   .sort('start_time', -1)
                   .skip((page - 1) * limit)
                   .limit(limit))
    
    total_seconds = sum(e.get('duration_seconds', 0) for e in entries)
    
    return jsonify({
        'entries': serialize_list(entries),
        'total_seconds': total_seconds,
        'total_hours': round(total_seconds / 3600, 2),
        'count': len(entries),
        'meta': {
            'page': page,
            'limit': limit,
            'total': total,
            'has_more': (page * limit) < total
        }
    }), 200


@time_bp.route('/entries/<entry_id>', methods=['GET'])
@jwt_required()
def get_time_entry(entry_id):
    """Get a specific time entry"""
    user_id = get_jwt_identity()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(entry_id)})
    except:
        return jsonify({'error': 'Invalid entry ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Time entry not found'}), 404
    
    # Only freelancer or project participants can view
    project = mongo.db.projects.find_one({'_id': entry['project_id']})
    if str(entry['freelancer_id']) != user_id and str(project.get('client_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'entry': serialize(entry)}), 200


@time_bp.route('/entries/<entry_id>', methods=['PUT'])
@jwt_required()
def update_time_entry(entry_id):
    """Update a time entry (description only, time can't be changed)"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(entry_id)})
    except:
        return jsonify({'error': 'Invalid entry ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Time entry not found'}), 404
    
    if str(entry['freelancer_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if entry.get('end_time') and not data.get('allow_edit_completed'):
        return jsonify({'error': 'Cannot edit completed time entries'}), 400
    
    update_fields = {}
    if 'description' in data:
        update_fields['description'] = data['description']
    
    mongo.db.time_entries.update_one(
        {'_id': ObjectId(entry_id)},
        {'$set': update_fields}
    )
    
    return jsonify({'message': 'Time entry updated'}), 200


@time_bp.route('/entries/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_time_entry(entry_id):
    """Delete a time entry"""
    user_id = get_jwt_identity()
    
    try:
        entry = mongo.db.time_entries.find_one({'_id': ObjectId(entry_id)})
    except:
        return jsonify({'error': 'Invalid entry ID'}), 400
    
    if not entry:
        return jsonify({'error': 'Time entry not found'}), 404
    
    if str(entry['freelancer_id']) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    mongo.db.time_entries.delete_one({'_id': ObjectId(entry_id)})
    
    return jsonify({'message': 'Time entry deleted'}), 200


# ════════════════════════════════════════════════════════════════
# TIME TRACKING REPORTS
# ════════════════════════════════════════════════════════════════

@time_bp.route('/report/daily', methods=['GET'])
@jwt_required()
def daily_report():
    """Get daily time report"""
    user_id = get_jwt_identity()
    date_str = request.args.get('date')
    
    if not date_str:
        date = datetime.date.today()
    else:
        try:
            date = datetime.datetime.fromisoformat(date_str).date()
        except:
            return jsonify({'error': 'Invalid date format'}), 400
    
    # Get entries for the date
    start = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
    
    entries = list(mongo.db.time_entries.find({
        'freelancer_id': ObjectId(user_id),
        'start_time': {'$gte': start, '$lte': end}
    }).sort('start_time', 1))
    
    total_seconds = sum(e.get('duration_seconds', 0) for e in entries)
    
    # Group by project
    by_project = {}
    for entry in entries:
        pid = str(entry['project_id'])
        if pid not in by_project:
            by_project[pid] = {'project_id': pid, 'entries': [], 'total_seconds': 0}
        by_project[pid]['entries'].append(serialize(entry))
        by_project[pid]['total_seconds'] += entry.get('duration_seconds', 0)
    
    return jsonify({
        'date': date.isoformat(),
        'total_seconds': total_seconds,
        'total_hours': round(total_seconds / 3600, 2),
        'by_project': list(by_project.values()),
        'entry_count': len(entries)
    }), 200


@time_bp.route('/report/summary', methods=['GET'])
@jwt_required()
def summary_report():
    """Get time tracking summary (last 30 days by default)"""
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    
    # Get all entries in the range
    entries = list(mongo.db.time_entries.find({
        'freelancer_id': ObjectId(user_id),
        'start_time': {'$gte': start_date}
    }))
    
    total_seconds = sum(e.get('duration_seconds', 0) for e in entries)
    
    # Group by project
    by_project = {}
    for entry in entries:
        pid = str(entry['project_id'])
        if pid not in by_project:
            by_project[pid] = 0
        by_project[pid] += entry.get('duration_seconds', 0)
    
    # Get project details
    projects_data = {}
    for pid in by_project:
        project = mongo.db.projects.find_one({'_id': ObjectId(pid)})
        if project:
            projects_data[pid] = {
                'project_id': pid,
                'title': project.get('title', 'Unknown'),
                'total_seconds': by_project[pid],
                'total_hours': round(by_project[pid] / 3600, 2)
            }
    
    return jsonify({
        'period_days': days,
        'total_seconds': total_seconds,
        'total_hours': round(total_seconds / 3600, 2),
        'by_project': list(projects_data.values()),
        'entry_count': len(entries)
    }), 200
