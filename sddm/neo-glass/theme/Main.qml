pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic
import NeoStatus 1.0

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#f8dbe9"
    focus: true

    readonly property color ink: "#fff7fc"
    readonly property color muted: "#e9d8e4"
    readonly property color accent: config.accentColor || "#a83f74"
    readonly property string username: users.count > 0 ? (users.currentValue || "") : manualUser.text.trim()
    property bool passwordShown: false
    property bool loggingIn: false
    property string loginMessage: ""
    property date now: new Date()
    property var statusProvider: deviceStatus

    function revealPassword() {
        if (loggingIn) return;
        passwordShown = true;
        Qt.callLater(function() {
            if (users.count === 0 && !manualUser.text.length) manualUser.forceActiveFocus();
            else password.forceActiveFocus();
        });
    }
    function dismissPassword() {
        if (loggingIn) return;
        password.text = "";
        loginMessage = "";
        passwordShown = false;
        root.forceActiveFocus();
    }
    function login() {
        if (!passwordShown) { revealPassword(); return; }
        if (loggingIn || !username) return;
        if (sessions.count === 0) {
            loginMessage = qsTr("No desktop session is available.");
            return;
        }
        loginMessage = "";
        loggingIn = true;
        sddm.login(username, password.text, Math.max(0, sessions.currentIndex));
        loginTimeout.start();
    }
    Keys.onReturnPressed: revealPassword()
    Keys.onEnterPressed: revealPassword()
    Keys.onEscapePressed: dismissPassword()

    Component.onCompleted: {
        users.currentIndex = Math.max(0, userModel.lastIndex);
        sessions.currentIndex = Math.max(0, sessionModel.lastIndex);
        root.forceActiveFocus();
    }
    DeviceStatus { id: deviceStatus }
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.now = new Date()
    }
    Timer {
        id: loginTimeout
        interval: 30000
        onTriggered: {
            root.loggingIn = false;
            root.loginMessage = qsTr("Sign-in timed out. Please try again.");
            password.text = "";
            password.forceActiveFocus();
        }
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            loginTimeout.stop();
            root.loggingIn = false;
            root.loginMessage = qsTr("Sign-in failed. Please try again.");
            password.text = "";
            if (root.passwordShown) password.forceActiveFocus();
        }
        function onLoginSucceeded() {
            loginTimeout.stop();
            root.loginMessage = qsTr("Welcome back.");
        }
        function onInformationMessage(message) { root.loginMessage = message; }
    }

    Item {
        id: wallpaperLayer
        anchors.fill: parent
        Image {
            objectName: "wallpaperImage"
            anchors.fill: parent
            source: Qt.resolvedUrl(config.background || "assets/background.jpg")
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            sourceSize.width: Math.min(3840, root.width * 2)
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: "#26754964" }
                GradientStop { position: 0.45; color: "#06754964" }
                GradientStop { position: 1; color: "#66754964" }
            }
        }
    }

    // Status floats directly over the wallpaper, without a menu bar surface.
    Row {
        id: statusRow
        objectName: "statusIndicators"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 22
        anchors.rightMargin: 30
        height: 24
        spacing: 20
        Item {
            objectName: "wifiIndicator"
            width: 25
            height: 24
            visible: root.statusProvider.wifiAvailable
            readonly property bool connected: root.statusProvider.wifiEnabled && root.statusProvider.wifiConnected
            readonly property int strength: root.statusProvider.wifiStrength
            Canvas {
                id: wifiCanvas
                anchors.fill: parent
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    ctx.lineWidth = 2.3;
                    ctx.lineCap = "round";
                    const limits = [0, 35, 70];
                    for (let i = 0; i < 3; i++) {
                        ctx.strokeStyle = parent.connected && parent.strength >= limits[i] ? "#fff7fc" : "#65fff7fc";
                        ctx.beginPath();
                        ctx.arc(12.5, 21, 6 + i * 5, Math.PI * 1.24, Math.PI * 1.76);
                        ctx.stroke();
                    }
                    ctx.fillStyle = parent.connected ? "#fff7fc" : "#65fff7fc";
                    ctx.beginPath(); ctx.arc(12.5, 20, 1.7, 0, Math.PI * 2); ctx.fill();
                    if (!root.statusProvider.wifiEnabled) {
                        ctx.strokeStyle = "#fff7fc";
                        ctx.beginPath(); ctx.moveTo(3, 3); ctx.lineTo(23, 22); ctx.stroke();
                    }
                }
                Connections {
                    target: root.statusProvider
                    function onChanged() { wifiCanvas.requestPaint(); }
                }
            }
            HoverHandler { id: wifiHover }
            ToolTip.visible: wifiHover.hovered
            ToolTip.text: !root.statusProvider.wifiEnabled ? qsTr("Wi-Fi off") : connected ? qsTr("Wi-Fi connected") : qsTr("Wi-Fi disconnected")
            Accessible.name: ToolTip.text
        }
        Row {
            objectName: "batteryIndicator"
            height: 24
            spacing: 7
            visible: root.statusProvider.batteryAvailable
            Text {
                text: root.statusProvider.batteryPercent + "%"
                color: root.ink
                font.family: config.fontFamily || "Inter"
                font.pixelSize: 12
                anchors.verticalCenter: parent.verticalCenter
            }
            Item {
                width: 30
                height: 16
                anchors.verticalCenter: parent.verticalCenter
                Rectangle {
                    width: 26; height: 14; y: 1; radius: 3
                    color: "transparent"; border.width: 1.3; border.color: "#ddfff7fc"
                    Rectangle {
                        x: 2.5; y: 2.5; height: 9; radius: 1
                        width: 21 * root.statusProvider.batteryPercent / 100
                        color: root.statusProvider.batteryPercent <= 15 && !root.statusProvider.batteryCharging ? "#ff8cad" : root.ink
                    }
                }
                Rectangle { x: 27; y: 5; width: 2.5; height: 6; radius: 1; color: "#ddfff7fc" }
                Text {
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: -2
                    visible: root.statusProvider.batteryCharging
                    text: "ϟ"; color: "#754964"; font.pixelSize: 20; font.bold: true
                }
            }
            HoverHandler { id: batteryHover }
            ToolTip.visible: batteryHover.hovered
            ToolTip.text: root.statusProvider.batteryCharging ? qsTr("Connected to power") : qsTr("On battery")
        }
    }

    Column {
        objectName: "dateAndClock"
        anchors.top: parent.top
        anchors.topMargin: Math.max(62, root.height * 0.105)
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: -2
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDate(root.now, "dddd, d MMMM")
            color: root.ink
            font.family: config.fontFamily || "Inter"
            font.pixelSize: Math.min(27, root.width / 30)
            font.weight: Font.DemiBold
            style: Text.Raised
            styleColor: "#30754964"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(root.now, "HH:mm")
            color: root.ink
            font.family: "Inter Display"
            font.pixelSize: Math.min(124, root.width / 10, root.height / 6)
            font.weight: Font.Bold
            font.letterSpacing: -5
            style: Text.Raised
            styleColor: "#30754964"
        }
    }

    Item {
        id: signIn
        objectName: "loginArea"
        width: Math.min(300, root.width - 40)
        height: users.count === 0 ? 264 : 230
        anchors.bottom: parent.bottom
        anchors.bottomMargin: root.height < 600 ? 40 : 65
        anchors.horizontalCenter: parent.horizontalCenter

        Button {
            id: identity
            objectName: "identityButton"
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: 132
            enabled: !root.loggingIn
            background: Item {}
            contentItem: Item {
                Item {
                    id: avatar
                    objectName: "userAvatar"
                    width: 82; height: 82
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        visible: !avatarCanvas.photoLoaded
                        color: "#edbad3"
                        Text {
                            anchors.centerIn: parent
                            text: root.username.substring(0, 1).toUpperCase() || "?"
                            color: "#754964"
                            font.family: "Inter"
                            font.pixelSize: 34
                        }
                    }
                    Canvas {
                        id: avatarCanvas
                        objectName: "avatarCanvas"
                        anchors.fill: parent
                        property bool photoLoaded: false
                        property url imageSource: config.avatarUser && config.avatar && root.username === config.avatarUser ? Qt.resolvedUrl(config.avatar) : ""
                        onImageSourceChanged: {
                            photoLoaded = false;
                            if (imageSource.toString().length) loadImage(imageSource, Qt.size(164, 164));
                            requestPaint();
                        }
                        onImageLoaded: {
                            photoLoaded = isImageLoaded(imageSource);
                            requestPaint();
                        }
                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.reset();
                            if (!photoLoaded) return;
                            ctx.save();
                            ctx.beginPath(); ctx.arc(width / 2, height / 2, width / 2, 0, Math.PI * 2); ctx.clip();
                            ctx.drawImage(imageSource, 0, 0, width, height);
                            ctx.restore();
                        }
                    }
                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        color: "transparent"
                        border.width: 1.5
                        border.color: identity.activeFocus ? "white" : "#80fff7fc"
                    }
                }
                Text {
                    objectName: "userName"
                    anchors.top: avatar.bottom
                    anchors.topMargin: 12
                    width: parent.width
                    text: users.count > 0 ? (users.currentText || root.username) : qsTr("Sign in")
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    color: root.ink
                    font.family: config.fontFamily || "Inter"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                    style: Text.Raised
                    styleColor: "#40754964"
                }
            }
            Accessible.name: qsTr("Sign in as %1").arg(root.username)
            onClicked: root.revealPassword()
        }

        Column {
            id: form
            objectName: "passwordForm"
            width: parent.width
            y: 145
            spacing: 9
            visible: root.passwordShown
            opacity: visible ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 180 } }
            TextField {
                id: manualUser
                objectName: "manualUsername"
                width: parent.width
                height: 38
                visible: users.count === 0
                enabled: !root.loggingIn
                placeholderText: qsTr("Username")
                placeholderTextColor: "#e9d8e4"
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 13
                leftPadding: 12
                selectByMouse: true
                background: Rectangle { radius: 12; color: "#40754964"; border.color: "#65fff7fc" }
                onAccepted: password.forceActiveFocus()
            }
            Item {
                width: parent.width
                height: 40
                TextField {
                    id: password
                    objectName: "passwordField"
                    anchors.fill: parent
                    placeholderText: root.loggingIn ? qsTr("Signing in…") : qsTr("Enter Password")
                    placeholderTextColor: "#e9d8e4"
                    echoMode: TextInput.Password
                    passwordCharacter: "•"
                    color: root.ink
                    font.family: "Inter"
                    font.pixelSize: 13
                    leftPadding: 13
                    rightPadding: 46
                    selectByMouse: true
                    enabled: !root.loggingIn
                    inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                    background: Rectangle {
                        radius: 12
                        color: "#60754964"
                        border.width: password.activeFocus ? 1.5 : 1
                        border.color: password.activeFocus ? "#dcfff7fc" : "#65fff7fc"
                    }
                    onAccepted: root.login()
                    Keys.onEscapePressed: root.dismissPassword()
                }
                Button {
                    id: submitButton
                    objectName: "signInButton"
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    width: 28; height: 28
                    enabled: !root.loggingIn && root.username.length > 0
                    text: "→"
                    contentItem: Text { text: submitButton.text; color: root.ink; font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    background: Rectangle { radius: 14; color: "#20fff7fc"; border.color: "#b0fff7fc" }
                    Accessible.name: qsTr("Sign in")
                    onClicked: root.login()
                }
            }
            Text {
                width: parent.width
                text: root.loginMessage || (typeof keyboard !== "undefined" && keyboard.capsLock ? qsTr("Caps Lock is on") : qsTr("Press Enter to sign in"))
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 11
            }
        }
    }

    // Secondary controls are exposed only after selecting the identity.
    Row {
        visible: root.passwordShown
        anchors.left: parent.left
        anchors.leftMargin: 24
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        spacing: 12
        GlassComboBox {
            id: users
            objectName: "userSelector"
            width: Math.min(150, root.width * 0.25)
            height: 30
            backdrop: wallpaperLayer
            model: userModel
            textRole: "realName"
            valueRole: "name"
            displayText: qsTr("Switch user")
            enabled: !root.loggingIn
            visible: count > 1
            contentItem: Text { text: users.displayText; color: root.ink; font: users.font; verticalAlignment: Text.AlignVCenter }
            indicator: Item {}
            background: Item {}
            popup.y: -popup.height - 8
            onCurrentIndexChanged: {
                password.text = "";
                root.loginMessage = "";
            }
            onActivated: root.revealPassword()
        }
        GlassComboBox {
            id: sessions
            objectName: "sessionSelector"
            width: Math.min(200, root.width * 0.3)
            height: 30
            backdrop: wallpaperLayer
            model: sessionModel
            enabled: !root.loggingIn
            contentItem: Text { text: sessions.displayText; color: root.ink; font: sessions.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
            indicator: Item {}
            background: Item {}
            popup.y: -popup.height - 8
            Accessible.name: qsTr("Desktop session")
        }
    }
    Button {
        id: powerButton
        objectName: "powerButton"
        visible: root.passwordShown
        anchors.right: parent.right
        anchors.rightMargin: 24
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        width: 72; height: 30
        text: qsTr("Power")
        enabled: !root.loggingIn
        contentItem: Text { text: powerButton.text; color: root.ink; font.family: "Inter"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Item {}
        onClicked: powerMenu.open()
    }
    Popup {
        id: powerMenu
        objectName: "powerMenu"
        focus: true
        x: root.width - width - 24
        y: root.height - height - 58
        width: 232
        padding: 10
        implicitHeight: powerItems.implicitHeight + 20
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: GlassPanel { backdrop: wallpaperLayer; cornerRadius: 22; tint: "#e6fdf1f8" }
        contentItem: Column {
            id: powerItems
            spacing: 4
            GlassButton { width: parent.width; text: qsTr("Sleep"); visible: sddm.canSuspend; onClicked: { powerMenu.close(); sddm.suspend(); } }
            GlassButton { width: parent.width; text: qsTr("Restart…"); visible: sddm.canReboot; onClicked: { powerMenu.close(); powerConfirm.restart = true; powerConfirm.open(); } }
            GlassButton { width: parent.width; text: qsTr("Shut down…"); visible: sddm.canPowerOff; onClicked: { powerMenu.close(); powerConfirm.restart = false; powerConfirm.open(); } }
        }
    }
    Popup {
        id: powerConfirm
        objectName: "powerConfirmation"
        property bool restart: false
        anchors.centerIn: Overlay.overlay
        width: Math.min(360, root.width - 40)
        padding: 24
        implicitHeight: confirmItems.implicitHeight + 48
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: GlassPanel { backdrop: wallpaperLayer; cornerRadius: 28; tint: "#e6fdf1f8" }
        contentItem: Column {
            id: confirmItems
            spacing: 18
            Text {
                text: powerConfirm.restart ? qsTr("Restart this computer?") : qsTr("Shut down this computer?")
                width: parent.width; wrapMode: Text.WordWrap
                color: "#452c3b"; font.family: "Inter"; font.pixelSize: 18; font.weight: Font.DemiBold
            }
            Row {
                spacing: 10
                GlassButton { objectName: "cancelPower"; width: (confirmItems.width - 10) / 2; text: qsTr("Cancel"); onClicked: powerConfirm.close() }
                GlassButton {
                    objectName: "confirmPower"
                    width: (confirmItems.width - 10) / 2
                    accented: true
                    text: powerConfirm.restart ? qsTr("Restart") : qsTr("Shut down")
                    onClicked: { powerConfirm.close(); if (powerConfirm.restart) sddm.reboot(); else sddm.powerOff(); }
                }
            }
        }
    }
}
