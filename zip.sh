set -v
repo=`basename $(pwd)`
(cd ..; zip -r -FS ~/projects/$repo $repo)
