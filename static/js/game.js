let room;  // Will store the room code
let playerType;  // Will store the player type
let isGameReady = false;

// Get room code from URL
const pathParts = window.location.pathname.split('/');
room = pathParts[pathParts.length - 1];
playerType = 'game';  // Since this is the game page

const socket = io();

// Connect to room
socket.emit('join', {
    room: room,
    player_type: playerType
});

// Add waiting message div
const waitingMessage = document.createElement('div');
waitingMessage.id = 'waiting-message';
waitingMessage.innerHTML = '<h2>Waiting for quiz player to join...</h2>';
waitingMessage.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';
document.body.appendChild(waitingMessage);

// Create game container
const gameContainer = document.createElement('div');
gameContainer.id = 'gameContainer';
gameContainer.style.display = 'none';
document.body.appendChild(gameContainer);

// Handle player connections
// Add this in both quiz.html and game.html socket event handlers
socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('player_joined', function(data) {
    console.log('Player joined event:', data);
    if (data.room_status.quiz_player && data.room_status.game_player) {
        console.log('Both players present, showing game');
        document.getElementById('waiting-message').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';  // or gameContainer for game.html
    } else {
        console.log('Waiting for other player');
        document.getElementById('waiting-message').style.display = 'block';
        document.getElementById('quiz-container').style.display = 'none';  // or gameContainer for game.html
    }
});

socket.on('player_left', function(data) {
    console.log('Player left event:', data);
    document.getElementById('waiting-message').style.display = 'block';
    document.getElementById('quiz-container').style.display = 'none';  // or gameContainer for game.html
    alert(`The ${data.player_type} player has left the game`);
});

socket.on('error', function(data) {
    console.error('Socket error:', data);
    alert(data.message);
});

const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'gameContainer',  // Add this line!
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};

let player;
let enemies;
let projectiles;
let healthText;
let scoreText;
let powerText;
let levelText;
let level = 0;
let powerUpLevel = 0;
let powerUpTime = 0;
let fireRateMultiplier = 0;
let score = 0;
let gameOver = false;
let lastFired = 0;
let currentProjectileType = 'basic'; // Track current projectile type
let background; // For background reference
let baseSpawnRate = 750;

function preload() {
    // Load all game assets
    this.load.image('player', '../static/assets/player.png');
    this.load.image('enemy', '../static/assets/enemy.png');
    this.load.image('bigEnemy', '../static/assets/bigEnemy.png');
    this.load.image('eggEnemy', '../static/assets/eggEnemy.png');
    this.load.image('stalkerEnemy', '../static/assets/stalkerEnemy.png');
    this.load.image('basic', '../static/assets/basic-projectile.png');
    this.load.image('laser', '../static/assets/laser-projectile.png');
    this.load.image('plasma', '../static/assets/plasma-projectile.png');
    this.load.image('background', '../static/assets/background.png')
    this.load.audio('die', '../static/assets/chicken_die_2.mp3');
    this.load.audio('hit', '../static/assets/hit_marker.mp3');
    this.load.audio('hurt', '../static/assets/take_damage.mp3');
    this.load.audio('gameOver', '../static/assets/game_over.mp3');
    this.load.audio('pew', '../static/assets/pew.mp3');
    this.load.audio('regen', '../static/assets/regen.mp3');
    this.load.audio('powerUp', '../static/assets/power_up.mp3');
}

function create() {

    socket.on('update_score', (data) => {
        player.health += data['score']
        if (healthText) {
            healthText.setText('Health: ' + player.health);
        }
        if (data['score'] > 0) this.regenSound.play();
    });

    socket.on('upgrade_projectile', () => {
        this.powerUpSound.play();
        powerUpLevel += 1
        powerUpTime = this.time.now;

    })

    // Calculate scale factor based on game size
    background = this.add.sprite(0, 0, 'background')
        .setOrigin(0, 0)
        .setDisplaySize(config.width, config.height);
    const gameWidth = this.sys.game.config.width;
    const baseSize = 32; // Desired base size for sprites

    // Create player with sprite instead of shape
    player = this.add.sprite(400, 300, 'player');
    player.setDisplaySize(48, 64); // Set exact pixel size
    this.physics.add.existing(player);
    player.body.setCollideWorldBounds(true);
    player.health = 100;
    player.facingAngle = 0; // Initialize facing angle


    // Create groups for enemies and projectiles
    enemies = this.physics.add.group();
    projectiles = this.physics.add.group();

    // Add collisions
    this.physics.add.overlap(projectiles, enemies, hitEnemy, null, this);
    this.physics.add.overlap(player, enemies, hitPlayer, null, this);

    // Add UI
    healthText = this.add.text(16, 16, 'Health: 100', { fontSize: '32px', fill: '#222222' });
    scoreText = this.add.text(16, 50, 'Score: 0', { fontSize: '32px', fill: '#222222' });
    powerText = this.add.text(16, 84, 'Power Level: 0', { fontSize: '32px', fill: '#222222' });
    levelText = this.add.text(16, 118, 'Difficulty Level: 0', { fontSize: '32px', fill: '#222222' });



    // Spawn enemies periodically
    this.time.addEvent({
        delay: baseSpawnRate - baseSpawnRate*level,
        callback: spawnEnemy,
        callbackScope: this,
        loop: true
    });

    // SFX
    this.dieSound = this.sound.add('die');
    this.hitSound = this.sound.add('hit');
    this.hurtSound = this.sound.add('hurt');
    this.gameOverSound = this.sound.add('gameOver');
    this.pewSound = this.sound.add('pew');
    this.regenSound = this.sound.add('regen');
    this.powerUpSound = this.sound.add('powerUp');
}

function update() {
    if (gameOver) return;

    // Player movement
    const cursors = this.input.keyboard.createCursorKeys();
    this.wKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
    this.aKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
    this.sKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
    this.dKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);
    const speed = 200 + 100*level;

    if (cursors.left.isDown || this.aKey.isDown) {
        player.body.setVelocityX(-speed);
    } else if (cursors.right.isDown || this.dKey.isDown) {
        player.body.setVelocityX(speed);
    } else {
        player.body.setVelocityX(0);
    }

    if (cursors.up.isDown || this.wKey.isDown) {
        player.body.setVelocityY(-speed);
    } else if (cursors.down.isDown || this.sKey.isDown) {
        player.body.setVelocityY(speed);
    } else {
        player.body.setVelocityY(0);
    }

    // Auto-fire at nearest enemy
    const time = this.time.now;
    if (time > lastFired) {
        fireProjectile.call(this, this.input.mousePointer);
        lastFired = time + 100 - 50*fireRateMultiplier;
    }
    let pointerX = this.input.activePointer.x;
    let pointerY = this.input.activePointer.y;
    let povAngle = Phaser.Math.Angle.Between(player.x, player.y, pointerX, pointerY) / Math.PI * 180;


    // console.log(povAngle);
    // Update enemies to follow player
    enemies.getChildren().forEach(enemy => {
        let enemyType = enemy["texture"]["key"]

        let enemyAngle = Phaser.Math.Angle.Between(player.x, player.y, enemy.x, enemy.y) / Math.PI * 180;
        let diffAngle = Math.abs(povAngle - enemyAngle)

        let base_speed = 70
        if (enemyType === "bigEnemy") base_speed *= 0.5
        else if (enemyType === "eggEnemy") base_speed *= 0.75
        else if (enemyType === "stalkerEnemy") {
            base_speed *= diffAngle > 60 ? 2.5 : 0;
        }
        this.physics.moveToObject(enemy, player, base_speed*(level+1));
    });

    const curTime = this.time.now;
    if (curTime > powerUpTime + 1000*10) {
        powerUpTime = curTime
        powerUpLevel--;
        powerUpLevel = Math.max(0, powerUpLevel);
    }
    powerText.setText('Power Level: ' + powerUpLevel);
    levelText.setText('Difficulty Level: ' + Math.round(level * 100) / 100);



    const levelsPerWeapon = 2;
    let weaponNum = Math.floor(powerUpLevel / levelsPerWeapon);
    fireRateMultiplier = powerUpLevel - levelsPerWeapon*weaponNum;
    if (weaponNum === 0) currentProjectileType = 'basic';
    else if (weaponNum === 1) {
        currentProjectileType = 'laser';
    }
    else if (weaponNum >= 2) {
        currentProjectileType = 'plasma';
    }
}

function spawnEnemy(x=null, y=null, enemyType=null) {
    // Spawn enemy at random edge of screen
    if (gameOver) return
    if (x && y) {

    }
    else
    {
        let dist;
        do {
            x = Math.random() * config.width;
            y = Math.random() * config.height;
            dist = Math.sqrt((x - player.x)**2+(y - player.y)**2);
        }
        while (dist / config.height < 0.5);
    }
    if (enemyType) {

    }
    else {
        enemyType = "enemy";
        enemyType = Math.random() < 0.1 + 0.25*level ? "stalkerEnemy" : enemyType
        enemyType = Math.random() < 0.1 + 0.1*level ? "bigEnemy" : enemyType
        enemyType = Math.random() < 0.1 + 0.15*level ? "eggEnemy" : enemyType
    }

    const enemy = this.add.sprite(x, y, enemyType);
    if (enemyType === "enemy") {
        enemy.setDisplaySize(48, 60); // Set enemy size
        enemy.health = 30
    }
    else if (enemyType === "bigEnemy") {
        let scale = 2;
        enemy.setDisplaySize(48 * scale, 60 * scale); // Set enemy size
        enemy.health = 120
    }
    else if (enemyType === "stalkerEnemy") {
        enemy.setDisplaySize(40, 60); // Set enemy size
        enemy.health = 20
    }
    else if (enemyType === "eggEnemy") {
        enemy.setDisplaySize(80, 80); // Set enemy size
        enemy.health = 60
    }
    this.physics.add.existing(enemy);
    enemies.add(enemy);
}

function fireProjectile(enemy) {
    const angle = Phaser.Math.Angle.Between(player.x, player.y, enemy.x, enemy.y);

    const projectile = this.add.sprite(player.x, player.y, currentProjectileType);

    // Different sizes and effects based on projectile type
    switch(currentProjectileType) {
        case 'basic':
            projectile.setDisplaySize(16, 16);
            break;
        case 'laser':
            projectile.setDisplaySize(20, 8);
            // Add blue tint
            //projectile.setTint(0x00ff00);
            break;
        case 'plasma':
            projectile.setDisplaySize(24, 24);
            // Add purple tint
            //projectile.setTint(0xff00ff);
            break;
    }

    this.physics.add.existing(projectile);
    projectiles.add(projectile);

    // Different speeds based on projectile type
    let speed = 300;
    if (currentProjectileType === 'laser') speed = 400;
    if (currentProjectileType === 'plasma') speed = 500;

    this.physics.moveTo(projectile, enemy.x, enemy.y, speed);

    // Destroy projectile after 2 seconds
    this.time.delayedCall(4000, () => {
        if (projectile && !projectile.destroyed) {
            projectile.destroy();
        }
    });
}

function hitEnemy(projectile, enemy) {
    if (projectile && !projectile.destroyed) {
        projectile.destroy();
    }

    // Different damage based on projectile type
    let damage = 10;
    switch(currentProjectileType) {
        case 'laser':
            damage = 20;
            break;
        case 'plasma':
            damage = 30;
            break;
    }

    enemy.health -= damage;
    this.hitSound.play();

    if (enemy.health <= 0) {
        enemy.destroy();
        score += 10;
        level += 0.025
        scoreText.setText('Score: ' + score);
        this.dieSound.play();

        let enemyType = enemy["texture"]["key"]
        if (enemyType === "eggEnemy") {
            for (let i = 0; i < 5; i ++) {
                let x = enemy.x + 100*(Math.random() - 0.5);
                let y = enemy.y + 100*(Math.random() - 0.5);
                spawnEnemy.call(this, x, y, "enemy");
            }
        }
    }


}

function hitPlayer(player, enemy) {
    enemy.destroy();
    player.health -= 10;
    healthText.setText('Health: ' + player.health);
    this.hurtSound.play();
    level /= 2;

    if (player.health <= 0) {
        gameOver = true;
        this.gameOverSound.play();
        this.add.text(config.width/2, config.height/2, 'Game Over', {
            fontSize: '64px',
            fill: '#fff'
        }).setOrigin(0.5);
    }

    enemies.getChildren().forEach(enemy => {
        let x = enemy.x;
        let y = enemy.y;
        let dist = Math.sqrt((x - player.x)**2+(y - player.y)**2);
        if (dist / config.height < 0.5) enemy.destroy();
    });

}

function findNearestEnemy() {
    let nearestEnemy = null;
    let shortestDistance = Infinity;

    enemies.getChildren().forEach(enemy => {
        const distance = Phaser.Math.Distance.Between(
            player.x, player.y, enemy.x, enemy.y
        );
        if (distance < shortestDistance) {
            shortestDistance = distance;
            nearestEnemy = enemy;
        }
    });

    return nearestEnemy;
}


new Phaser.Game(config);