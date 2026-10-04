pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic

Button {
    id: control
    property bool accented: false
    property color ink: "#452c3b"
    implicitHeight: 44
    implicitWidth: 120
    hoverEnabled: true
    font.family: "Inter"
    font.pixelSize: 14
    activeFocusOnTab: true
    opacity: enabled ? 1 : 0.5

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.accented ? "#fff9fc" : control.ink
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: height / 2
        color: control.accented ? (control.down ? "#913660" : control.hovered ? "#ba5288" : "#a83f74")
                               : (control.down ? "#88e9a9cb" : control.hovered ? "#aaffffff" : "#65ffffff")
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? "#a83f74" : "#aafff9fd"
        Behavior on color { ColorAnimation { duration: 140 } }
    }
}
