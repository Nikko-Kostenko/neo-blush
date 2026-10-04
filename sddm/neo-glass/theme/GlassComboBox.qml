pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    required property Item backdrop
    implicitWidth: 260
    implicitHeight: 42
    font.family: "Inter"
    font.pixelSize: 14
    textRole: "name"
    leftPadding: 15
    rightPadding: 35
    activeFocusOnTab: true
    hoverEnabled: true

    contentItem: Text {
        text: control.displayText
        font: control.font
        color: "#452c3b"
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text {
        x: control.width - width - 15
        anchors.verticalCenter: parent.verticalCenter
        text: "⌄"
        color: "#87697c"
        font.pixelSize: 18
    }
    background: Rectangle {
        radius: 15
        color: control.hovered ? "#aaffffff" : "#65ffffff"
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? "#a83f74" : "#aafff9fd"
    }
    delegate: ItemDelegate {
        id: entry
        required property int index
        required property var model
        width: control.width - 16
        height: 40
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: entry.model[control.textRole] || entry.model.name || ""
            color: "#452c3b"
            font: control.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 10
            color: entry.highlighted ? "#85e399bf" : "transparent"
        }
    }
    popup: Popup {
        focus: true
        y: control.height + 8
        width: control.width
        padding: 8
        implicitHeight: Math.min(260, contentItem.implicitHeight + 16)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: GlassPanel {
            backdrop: control.backdrop
            cornerRadius: 20
            tint: "#e6fdf1f8"
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            spacing: 3
            ScrollIndicator.vertical: ScrollIndicator { }
        }
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 150 }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 100 }
        }
    }
}
