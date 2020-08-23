#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.

XButton1::
    MouseClick
    MouseClick
    MouseGetPos, X, Y
    Send {Shift DOWN}
    Sleep 10
    MouseClick
    Send {Shift UP}
    Send ^a^c{Escape}
    Sleep 100
    script := "main.pyw"
    Run %script% "%clipboard%" %X% %Y%
