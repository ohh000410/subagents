$inputText = [System.IO.StreamReader]::new([Console]::OpenStandardInput(), [System.Text.UTF8Encoding]::new($false)).ReadToEnd()
$hookInput = $inputText | ConvertFrom-Json
$agentType = [string]$hookInput.agent_type
# 공개판 플러그인 훅(hooks/hooks.json)에서는 이름이 "<플러그인>:<에이전트>" 로 오고, 본문·정책은 플러그인 폴더 안에 있다
$pluginRoot = $env:CLAUDE_PLUGIN_ROOT
if ($pluginRoot) {
    $agentType = $agentType.Split(':')[-1]
}

if ($agentType -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
    exit 0
}

# 공통 계약 + 본문. 메모리(정책·목차)는 inject-agent-memory.ps1 — Claude 는 훅 글 하나가 1만 자를 넘으면 앞 2,000자만
# 보이고 나머지는 파일로 빼서(읽으라는 지시 없음) 둘로 나눴다(2026-10-23)
$utf8 = [System.Text.UTF8Encoding]::new($false)
$sourceRoot = Split-Path $PSScriptRoot -Parent
$agentRoot = if ($pluginRoot) { Join-Path $sourceRoot $agentType } else { Join-Path (Join-Path $sourceRoot 'agents') $agentType }
$agentBody = Join-Path $agentRoot 'AGENT.md'
$referenceRoot = Join-Path $agentRoot 'references'
$contract = Join-Path (Join-Path $sourceRoot 'policies') 'common_agent_contract.md'
$sections = @()

if (Test-Path -LiteralPath $agentBody -PathType Leaf) {
    # 공통 계약은 전문 에이전트(본문이 있는 에이전트) 모두에게 — 본문마다 "시작 시 읽기" 로 두던 것을 주입으로(2026-10-19)
    $sections += "## Common agent contract`n`n" + [System.IO.File]::ReadAllText($contract, $utf8)
    $bodyHeader = "## Agent body`n`n"
    if (Test-Path -LiteralPath $referenceRoot -PathType Container) {
        $bodyHeader += "Reference root: $referenceRoot`n`n"
    }
    $sections += $bodyHeader + [System.IO.File]::ReadAllText($agentBody, $utf8)
}

if ($sections.Count -eq 0) {
    exit 0
}

$additionalContext = "# SubagentStart injected context`n`n" + ($sections -join "`n`n---`n`n")
if ($pluginRoot) {
    # 배포판 글의 ${CLAUDE_PLUGIN_ROOT} — 에이전트 파일 안이면 Claude 가 바꿔 주지만 훅이 넣는 글은 그대로 들어간다
    $additionalContext = $additionalContext.Replace('${CLAUDE_PLUGIN_ROOT}', $pluginRoot)
}
$output = @{
    hookSpecificOutput = @{
        hookEventName = 'SubagentStart'
        additionalContext = $additionalContext
    }
}

[Console]::OutputEncoding = $utf8
[Console]::Out.Write(($output | ConvertTo-Json -Depth 5 -Compress))

