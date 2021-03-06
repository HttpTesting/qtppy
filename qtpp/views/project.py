from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,jsonify
)
from werkzeug.exceptions import abort
from qtpp.views.auth import login_required

from qtpp import db
from qtpp.libs.framework.operate_db import OperationDB
from qtpp.libs.framework.constant import Const
from qtpp.models.project import Project, TestSuite


bp = Blueprint('project', __name__, url_prefix='/project')
odb = OperationDB()



@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create_project():
    '''
    创建项目
    '''
    if request.method == 'POST':
        project_name = request.json['name']
        p_desc = request.json['desc']
     
        if not g.user.uid:
            # flash(error)
            return jsonify(Const.NOT_LOGIN_DICT)

        projects = Project(project_name, g.user.username, g.user.uid, p_desc)
        odb.add(projects)

        
        Const.SUCCESS_DICT['errmsg'] = '创建项目成功.'
        Const.SUCCESS_DICT['res'] = {
            "project_name": project_name, 
            "p_id": projects.p_id,
            "p_desc": projects.p_desc,
            "p_creator": projects.p_creator,
            "p_status": projects.p_status,
            "p_createtime": projects.create_time
        }
        return jsonify(Const.SUCCESS_DICT)
 

    return abort(404)


@bp.route('/delete', methods=('GET', 'POST'))
@login_required
def delete_project():
    '''
    删除项目,级联测试集也会删除
    args:
        p_id: 项目ID
    '''
    if request.method == 'POST':
        error = None

        if not g.user.uid:
            error = 'this is not required.'
        
        # 授权
        if error is not None:
            return jsonify(Const.NOT_LOGIN_DICT)


        p_id_lst = request.json

        del_res = []
        for p_id in p_id_lst['p_id']:
            dt = odb.delete(Project, 'p_id', int(p_id))
            del_res.append({"p_id": p_id, "p_name": dt.p_name})
            

        Const.SUCCESS_DICT['errmsg'] = '删除成功'
        Const.SUCCESS_DICT['res'] = {
            'project': del_res
        }
        return jsonify(Const.SUCCESS_DICT)

    return abort(404)


@bp.route('/update', methods=('GET', 'POST'))
@login_required
def update_project_info():
    '''
    更新项目
    method: post
    params: p_id, name
    '''
    if request.method == 'POST':
        error = None

        if not g.user.uid:
            error = ''
        
        # 授权
        if error is not None:
            return jsonify(Const.NOT_LOGIN_DICT)

        params =  request.args

        # 按照项目ID，更新项目名称
        dt = odb.update(
            Project, 'p_id', 
            int(params['p_id']), 
            p_name=params['name']
        )

        Const.SUCCESS_DICT['errmsg'] = '更新成功'
        Const.SUCCESS_DICT['res'] = {
            'project': {
                "p_id": dt.p_id,
                "new_p_name": dt.p_name
            }
        }
        return jsonify(Const.SUCCESS_DICT)

    return abort(404)


@bp.route('/getall/<int:id>', methods=('GET', 'POST'))
@login_required
def get_project_or_suite_list(id):
    '''
    获取所有项目列表或项目下测试集
    '''
    if request.method == 'POST':
        error = None

        if not g.user.uid:
            error = 'this is not required.'
        
        if error is not None:
            return jsonify(Const.NOT_LOGIN_DICT)

        '''
        true获取项目内容，false获取测试集内容
        true_bool = (项目ID, 项目名称, 项目model对象， 用户ID字段，用户ID)
        false_bool = (测试集ID， 测试集名称，测试集model对象，项目ID字段，项目ID)
        '''
        true_bool = ('p_id', 'p_name', 'Project', 'user_id', g.user.uid)
        
        # id为1获取项目，否则获取测试集
        args = true_bool if id == 1 else ('sid', 's_name', 'TestSuite', 'p_id', int(request.json['p_id']))

        #通过args[2] 来选择数据模型对象
        # all_data = odb.query_all(eval(args[2]))
        # 分页展示
        paginate = odb.query_all_paginate(
            eval(args[2]), 
            page=int(request.args.get('page', 1))
        )

        Const.SUCCESS_DICT['errmsg'] = 'SUCCESS'
        Const.SUCCESS_DICT['res'] = {
            "prev_num": paginate.prev_num,
            "per_page": paginate.per_page,
            "pages": paginate.pages,
            "total": paginate.total,
            "page": paginate.page,
            "next_page": paginate.next_num,
            "project": [
                {'%s'%args[0]:getattr(i, args[0]), "%s"%args[1]:getattr(i, args[1])} 
                for i in paginate.items 
                    if getattr(i, args[3]) == args[4]
                ]
        }

        return jsonify(Const.SUCCESS_DICT)

    return abort(404)


@bp.route('/suite/getlist', methods=('GET', 'POST'))
@login_required
def get_suite_by_pid():
    '''
    根据项目id获取，该项目下的所有测试集
    '''
    if request.method == 'POST':
        error = None
        if not g.user.uid:
            error = 'is not required.'

        if error is not None:
            return jsonify(Const.NOT_LOGIN_DICT)

        pid = request.args.get('p_id', False)
        if not pid:
            Const.SUCCESS_DICT['errcode'] = 1002
            Const.SUCCESS_DICT['errmsg'] = Const.ERROR_DICT['1002']

            return jsonify(Const.SUCCESS_DICT)

        else:
            # suite_data = odb.query_per_all(TestSuite, 'p_id', int(pid))
            # 分页
            paginate = odb.query_per_paginate(
                TestSuite, 
                'p_id', 
                int(pid), 
                page=int(request.args.get('page', 1)),
                per_page=int(request.args.get('pre_page', 10))
            )

            Const.SUCCESS_DICT['errmsg'] = 'SUCCESS'
            Const.SUCCESS_DICT['res'] = {
                "prev_num": paginate.prev_num,
                "per_page": paginate.per_page,
                "pages": paginate.pages,
                "total": paginate.total,
                "page": paginate.page,
                "next_page": paginate.next_num,
                "suite":[{"sid": sd.sid,"s_name": sd.s_name} for sd in paginate.items],
                "count": len(paginate.items)
            }
            return jsonify(Const.SUCCESS_DICT)

    return abort(404)


@bp.route('/suite/create', methods=('GET', 'POST'))
@login_required
def create_suite():
    '''
    创建测试集
    '''
    if request.method == 'POST':

        error = None

        if not g.user.uid:
            error = '尚未登录.'

        if error is not None:
            return jsonify(
                {"errcode": 1001, "errmsg": error}
            )

        req_args = request.json

        test_suite = TestSuite(
                req_args['s_name'], 
                g.user.username, 
                req_args['project_id']
        )
        odb.add(test_suite)

        return jsonify(
            {
                "errcode": 0, 
                "errmsg": "新建测试集成功.", 
                'res':{
                    "suite_id": test_suite.sid, 
                    "suite_name": req_args['s_name'], 
                    "project_id": req_args['project_id']
                }
            }
        )
    return abort(404)


@bp.route('/suite/delete', methods=('GET', 'POST'))
@login_required
def delete_suite():
    '''
    根据测试集ID，删除测试集
    '''
    if request.method == 'POST':
        error = None

        if not g.user.uid:
            error = '尚未登录'
        
        if error is not None:
            return jsonify(
                {"errcode": 1001, "errmsg": error}
            )

        s_id_lst = request.json

        del_res = []
        for sid in s_id_lst['sid']:

            dt = odb.delete(TestSuite, 'sid', int(sid))
            del_res.append({"sid": int(sid), "s_name": dt.s_name, "p_id": dt.p_id})
            

        Const.SUCCESS_DICT['errmsg'] = '删除成功'
        Const.SUCCESS_DICT['res'] = {
            'suite': del_res
        }
        return jsonify(Const.SUCCESS_DICT)

    
    return abort(404)


@bp.route('/suite/update', methods=['GET', 'POST'])
@login_required
def suite_update():
    '''
    更新测试集信息
    '''
    if request.method == 'POST':

        if not g.user.uid:
            return jsonify(Const.NOT_LOGIN_DICT)
        
        req_data_json = request.json

        suite_dt = odb.update(
            TestSuite, 
            'sid', 
            int(req_data_json['sid']),
            s_name=req_data_json['s_name']
        )

        Const.SUCCESS_DICT['errmsg'] = '更新成功'
        Const.SUCCESS_DICT['res'] = {
            'suite': {
                "sid": suite_dt.sid,
                "new_s_name": suite_dt.s_name,
                "p_id": suite_dt.p_id
            }
        }

        return jsonify(Const.SUCCESS_DICT)

    return abort(404)