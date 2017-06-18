#!/usr/bin/env bash
set -e -x

git add --all

AUTHOR=$(git --no-pager show -s --format='%an <%ae>' HEAD)
export GIT_AUTHOR_NAME=$(git --no-pager show -s --format='%an' HEAD)
export GIT_AUTHOR_EMAIL=$(git --no-pager show -s --format='%ae' HEAD)

git status

if [ "${TRAVIS_EVENT_TYPE}" == "push" ] ; then
    # Split the organisation out of the slug. See https://stackoverflow.com/a/5257398/741316 for description.
    ORG=(${TRAVIS_REPO_SLUG//\// })
    DEPLOY_KEY=.github/deploy_key.${ORG}.enc

    if [ ! -f ${DEPLOY_KEY} ]; then
        echo "Not syncing, the deploy key ${DEPLOY_KEY} does not exist"
    else
        pip install doctr --quiet
        doctr deploy --built-docs . \
            --deploy-branch-name ${TRAVIS_BRANCH} . \
            --key-path ${DEPLOY_KEY} \
            --no-require-master \
            --no-sync
    fi
fi
