<#
.SYNOPSIS
    Fast-forward this fork's mirror branches from xbmc/xbmc.

.DESCRIPTION
    The GitHub Action in .github/workflows/sync-upstream.yml already does this
    every day. This script is the manual/local equivalent -- useful when you want
    the source on THIS machine up to date right now.

    It pushes upstream refs straight to the fork:

        git push origin upstream/master:refs/heads/master

    That is a server-side fast-forward. It never checks anything out, so your
    working tree and any branch you have in progress are left completely alone,
    and it works even with the blobless (--filter=blob:none) clone.

.PARAMETER RepoPath
    Path to the xbmc clone. Defaults to D:\Kodi\xbmc.

.PARAMETER Branches
    Mirror branches to sync. Defaults to master, Omega, Nexus.

.PARAMETER UpdateLocal
    Also fast-forward your local checked-out branch if it is one of the mirrors
    and has no local commits.

.EXAMPLE
    .\sync-upstream.ps1
    .\sync-upstream.ps1 -Branches master -UpdateLocal
#>
[CmdletBinding()]
param(
    [string]   $RepoPath = 'D:\Kodi\xbmc',
    [string[]] $Branches = @('master', 'Omega', 'Nexus'),
    [switch]   $UpdateLocal
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
    throw "Not a git repo: $RepoPath"
}
Push-Location $RepoPath
try {
    # --- sanity: make sure 'upstream' points where we think it does ----------
    $upstreamUrl = (git remote get-url upstream 2>$null)
    if (-not $upstreamUrl) {
        Write-Host "adding missing 'upstream' remote..." -ForegroundColor Yellow
        git remote add upstream https://github.com/xbmc/xbmc.git
        $upstreamUrl = (git remote get-url upstream)
    }
    Write-Host "origin  : $(git remote get-url origin)"
    Write-Host "upstream: $upstreamUrl`n"

    Write-Host 'fetching upstream...' -ForegroundColor Cyan
    git fetch upstream --filter=blob:none --tags --prune
    if ($LASTEXITCODE -ne 0) { throw 'git fetch upstream failed' }

    $current = (git rev-parse --abbrev-ref HEAD)
    $results = @()

    foreach ($b in $Branches) {
        # Does the branch actually exist upstream?
        git show-ref --verify --quiet "refs/remotes/upstream/$b"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "skip $b (not present upstream)" -ForegroundColor DarkGray
            $results += [pscustomobject]@{ Branch = $b; Status = 'absent upstream'; Commit = '' }
            continue
        }

        $target = (git rev-parse "upstream/$b")
        $before = (git rev-parse "origin/$b" 2>$null)

        if ($before -eq $target) {
            Write-Host "= $b already current ($($target.Substring(0,10)))" -ForegroundColor DarkGray
            $results += [pscustomobject]@{ Branch = $b; Status = 'already current'; Commit = $target.Substring(0, 10) }
        }
        else {
            Write-Host "-> pushing $b : $($before ?? 'new')  ->  $($target.Substring(0,10))" -ForegroundColor Green
            # No --force: if this is not a fast-forward we WANT it to fail loudly,
            # because that means the mirror branch picked up commits it shouldn't have.
            git push origin "upstream/${b}:refs/heads/$b"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   !! $b is not fast-forwardable -- it has diverged from upstream." -ForegroundColor Red
                Write-Host "      Mirror branches must stay pristine. To discard local history:" -ForegroundColor Red
                Write-Host "      git push origin upstream/${b}:refs/heads/$b --force" -ForegroundColor Red
                $results += [pscustomobject]@{ Branch = $b; Status = 'DIVERGED'; Commit = $target.Substring(0, 10) }
                continue
            }
            $results += [pscustomobject]@{ Branch = $b; Status = 'synced'; Commit = $target.Substring(0, 10) }
        }

        # Optionally move the local branch too.
        if ($UpdateLocal -and $current -eq $b) {
            $ahead = (git rev-list --count "upstream/$b..$b")
            if ($ahead -eq '0') {
                git merge --ff-only "upstream/$b" | Out-Null
                Write-Host "   local '$b' fast-forwarded" -ForegroundColor Green
            }
            else {
                Write-Host "   local '$b' has $ahead local commit(s) - left untouched" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ''
    $results | Format-Table -AutoSize
}
finally {
    Pop-Location
}
