from sanic import Sanic
from sanic import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, redirect
from typing import Any

from ..forms.register import (
    SignUpForm,
    common_email,
    common_nickname,
    check_signup_form,
    SignUpModel,
)
from ...password import pswd_bcrypt_adapter
from ....infra.web.blueprints.plain.render import launch_render as render
from ....infra.web.blueprints.plain.path import plain_static
from ....infra.web.settings.location import CONFIG_LOCATION, REQUEST_CONTEXT_LOCATION
from ....infra.web.dependency.database import DatabaseDep
from ....infra.helpers.config.app import AppConfig
from ....infra.helpers.config.page import PageConfig
from ....infra.deps.database.dao.user import defaultUserRepo, UserDAO
from ....application.user.usecase.register import RegisterUsecase


async def registerpresentation(request: Request) -> HTTPResponse:
    request.ctx.page_config.load_items(role="SignUp")

    return await render(request, "register.html", context=dict(form=SignUpForm()))


async def register(request: Request, dep: DatabaseDep) -> HTTPResponse:
    # Check.
    form_data = request.form
    if not form_data:
        return await render(request, "register.html", context=dict(form=SignUpForm()))
    data_lists = {
        k: form_data.get(k)
        for k in ["nickname", "email", "password", "confirm", "remember"]
    }
    model = check_signup_form(SignUpForm(data=data_lists))
    if isinstance(model, SignUpForm):
        return await render(request, "register.html", context=dict(form=model))

    # Query.
    service = RegisterUsecase(
        repo=defaultUserRepo(
            session=dep.session_maker, password_service=pswd_bcrypt_adapter
        )
    )
    user = await service(model)

    request.ctx.page_config.load_items()

    # return redirect("/user/register")
    return await render(request, "register.html", context=dict(form=SignUpForm()))


def formcheck(form):
    ...
