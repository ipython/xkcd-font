#!/usr/bin/env bash
set -e -x

git add --all

AUTHOR=$(git --no-pager show -s --format='%an <%ae>' HEAD)
export GIT_AUTHOR_NAME=$(git --no-pager show -s --format='%an' HEAD)
export GIT_AUTHOR_EMAIL=$(git --no-pager show -s --format='%ae' HEAD)

git status

if [ "${TRAVIS_EVENT_TYPE}" == "push" ] ; then
    pip install doctr --quiet
    doctr deploy --built-docs . \
        --deploy-branch-name ${TRAVIS_BRANCH} . \
        --key-path .github/deploy_key.enc \
        --no-require-master \
        --no-sync
fi
