from flask import Blueprint

from filedrop.srv.routes import apiv1, healthcheck

# define the blueprint->url prefix mapping
BLUEPRINTS: list[tuple[Blueprint, str]] = [(apiv1.bp, "/api/v1"), (healthcheck.bp, "/")]
