#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.

run_()
{
    Sleep 50
    if clipboard
        Run "main.exe" "%clipboard%"
}

!XButton1::
    Send ^a^c{Escape}
    run_()
    return

^XButton1::
    Send ^c
    run_()
    return
    
