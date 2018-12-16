set -v
git gc
repo=`basename $(pwd)`
(cd ..; zip -r -FS ~/projects/$repo $repo)
