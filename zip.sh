repo=`basename $(pwd)`
set -v
(cd ..; zip -r -FS ~/projects/$repo $repo)
