pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Effects

Item {
    id: panel
    required property Item backdrop
    property real cornerRadius: 28
    property color tint: "#a8faeaf1"
    property real blurAmount: 0.85
    readonly property bool effectsAvailable: panel.GraphicsInfo.api !== GraphicsInfo.Software

    // Sample only the wallpaper beneath this panel, never the foreground UI.
    ShaderEffectSource {
        id: sample
        anchors.fill: parent
        sourceItem: panel.backdrop
        sourceRect: {
            const backdropWidth = panel.backdrop.width;
            const backdropHeight = panel.backdrop.height;
            const origin = panel.mapToItem(panel.backdrop, 0, 0);
            return Qt.rect(origin.x, origin.y, panel.width, panel.height);
        }
        textureSize: Qt.size(Math.max(1, panel.width / 2), Math.max(1, panel.height / 2))
        live: true
        visible: false
    }

    Rectangle {
        id: mask
        anchors.fill: parent
        radius: panel.cornerRadius
        color: "white"
        layer.enabled: true
        visible: false
    }

    MultiEffect {
        anchors.fill: parent
        source: sample
        blurEnabled: true
        blurMax: 48
        blur: panel.blurAmount
        autoPaddingEnabled: false
        maskEnabled: true
        maskSource: mask
        visible: panel.effectsAvailable
    }

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: panel.cornerRadius
        color: panel.tint
        border.width: 1
        border.color: "#d9fff9fd"
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.lighter(panel.tint, 1.06) }
            GradientStop { position: 1; color: panel.tint }
        }
        layer.enabled: panel.effectsAvailable
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: "#3f1b32"
            shadowOpacity: 0.18
            shadowBlur: 0.7
            shadowVerticalOffset: 10
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: Math.max(0, panel.cornerRadius - 2)
        color: "transparent"
        border.width: 1
        border.color: "#40ffffff"
    }
}
