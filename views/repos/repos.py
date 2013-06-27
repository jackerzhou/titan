#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from flask import g, request, redirect, url_for, abort

from utils import code
from utils.jagare import get_jagare
from utils.repos import repo_required
from utils.account import login_required
from utils.helper import MethodView, Obj
from utils.validators import check_reponame
from utils.organization import member_required

from query.account import get_user
from query.repos import create_repo, update_repo,transport_repo, \
        delete_repo, get_repo_watcher
from query.organization import get_teams_by_ogranization, get_team_member, \
        get_team_by_name, get_organization_member

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    teams=self.get_joined_teams(organization)
                )

    def post(self, organization, member):
        repopath = request.form.get('path', '')
        name = request.form.get('name', '')
        summary = request.form.get('summary', '')
        teamname = repopath.strip('/').split('/', 1)[0]

        if not check_reponame(name):
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_NAME_INVALID, \
                    )

        team = get_team_by_name(organization.id, teamname) if teamname else None
        if teamname and not team:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = code.REPOS_PATH_INVALID, \
                    )

        path = os.path.join(teamname, '%s.git' % name)
        repo, error = create_repo(name, path, g.current_user, organization, team=team, summary=summary)
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        teams=self.get_joined_teams(organization), \
                        error = error, \
                    )

        view_url = url_for('repos.view', git=organization.git, rname=name)
        if teamname:
            view_url = url_for('repos.view', git=organization.git, tname=teamname, rname=name)
        return redirect(view_url)

    def get_joined_teams(self, organization):
        for team in get_teams_by_ogranization(organization.id):
            if not get_team_member(team.id, g.current_user.id):
                continue
            yield team

class View(MethodView):
    decorators = [repo_required(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        watcher = get_repo_watcher(g.current_user.id, repo.id)
        jagare = get_jagare(repo.id, repo.parent)
        version = kwargs.get('version', 'master')
        path = kwargs.get('path', '')
        tree = jagare.ls_tree(repo.get_real_path(), path=path, version=version)
        if not tree:
            raise abort(404)
        team = kwargs.get('team', None)
        tname = team.name if team else None
        tree = self.render_tree(
                    tree, version, organization.git, \
                    tname, repo.name
                )
        return self.render_template(
                    member=member, repo=repo, \
                    organization=organization, \
                    watcher=watcher, \
                    tree=tree, \
                    **kwargs
                )

    def render_tree(self, tree, version, git, tname, rname):
        for d in tree['data']:
            data = Obj()
            if d['type'] == 'tree':
                data.url = url_for('repos.view', git=git, tname=tname, rname=rname, version=version, path=d['path'])
            elif d['type'] == 'blob':
                #TODO blob reader
                data.url = '#'
            else:
                continue
            data.name = d['name']
            data.sha = d['sha']
            yield data

class Setting(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        return self.render_template(
                    member=member, repo=repo, organization=organization, \
                    **kwargs
                )

    def post(self, organization, member, repo, **kwargs):
        name = request.form.get('name')
        if name != repo.name:
            error = update_repo(organization, repo, name, kwargs.get('team', None))
            if error:
                return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error = error, \
                        **kwargs
                )

        return redirect(url_for('repos.setting', \
            git=organization.git, rname=repo.name, \
            tname=kwargs['team'].name if kwargs.get('team') else None))

class Transport(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        return self.render_template(
                    member=member, repo=repo, organization=organization, \
                    **kwargs
                )

    def post(self, organization, member, repo, **kwargs):
        name = request.form.get('name')
        user = get_user(name)
        if not user:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.ACCOUNT_NO_SUCH_USER, \
                        **kwargs
                    )
        if user.id == repo.uid:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.REPOS_CANT_TRANSPORT_SELF, \
                        **kwargs
                    )
        is_member = get_organization_member(organization.id, user.id)
        if not is_member:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=code.ORGANIZATION_MEMBER_NOT_EXISTS, \
                        **kwargs
                    )

        team = kwargs.get('team', None)
        tname = team.name if team else None
        error = transport_repo(organization, user, repo, team)
        if error:
            return self.render_template(
                        member=member, repo=repo, organization=organization, \
                        error=error, \
                        **kwargs
                    )
        return redirect(url_for('repos.transport', git=organization.git, rname=repo.name, \
            tname=tname))

class Delete(MethodView):
    decorators = [repo_required(admin=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, repo, **kwargs):
        team = kwargs.get('team', None)
        delete_repo(organization, repo, team)
        return redirect(url_for('organization.view', git=organization.git))

