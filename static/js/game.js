const socket = io();

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
let score = 0;
let gameOver = false;
let lastFired = 0;
let currentProjectileType = 'basic'; // Track current projectile type
let background; // For background reference

function preload() {
    // Load all game assets
    this.load.image('player', 'static/assets/player.png');
    this.load.image('enemy', 'static/assets/enemy.png');
    this.load.image('basic', 'static/assets/basic-projectile.png');
    this.load.image('laser', 'static/assets/laser-projectile.png');
    this.load.image('plasma', 'static/assets/plasma-projectile.png');
    this.load.image('background', 'static/assets/background.png')
}

function create() {

    socket.on('update_score', (data) => {
        player.health += data['score']
        if (healthText) {
            healthText.setText('Health: ' + player.health);
        }
    });

    // Calculate scale factor based on game size
    background = this.add.tileSprite(0, 0, config.width, config.height, 'background')
        .setOrigin(0, 0);
    const gameWidth = this.sys.game.config.width;
    const baseSize = 32; // Desired base size for sprites

    // Create player with sprite instead of shape
    player = this.add.sprite(400, 300, 'player');
    player.setDisplaySize(baseSize, baseSize); // Set exact pixel size
    this.physics.add.existing(player);
    player.body.setCollideWorldBounds(true);
    player.health = 100;

    // Create groups for enemies and projectiles
    enemies = this.physics.add.group();
    projectiles = this.physics.add.group();

    // Add collisions
    this.physics.add.overlap(projectiles, enemies, hitEnemy, null, this);
    this.physics.add.overlap(player, enemies, hitPlayer, null, this);

    // Add UI
    healthText = this.add.text(16, 16, 'Health: 100', { fontSize: '32px', fill: '#fff' });
    scoreText = this.add.text(16, 50, 'Score: 0', { fontSize: '32px', fill: '#fff' });

    // Add quiz button
    const quizBtn = this.add.text(600, 16, 'Get Question', { 
        fontSize: '24px', 
        backgroundColor: '#444',
        padding: { x: 10, y: 5 },
        fill: '#fff' 
    })
    .setInteractive()
    .on('pointerdown', () => showQuestion());

    // Spawn enemies periodically
    this.time.addEvent({
        delay: 400,
        callback: spawnEnemy,
        callbackScope: this,
        loop: true
    });
}

function update() {
    if (gameOver) return;

    // Player movement
    const cursors = this.input.keyboard.createCursorKeys();
    const speed = 200;

    if (cursors.left.isDown) {
        player.body.setVelocityX(-speed);
    } else if (cursors.right.isDown) {
        player.body.setVelocityX(speed);
    } else {
        player.body.setVelocityX(0);
    }

    if (cursors.up.isDown) {
        player.body.setVelocityY(-speed);
    } else if (cursors.down.isDown) {
        player.body.setVelocityY(speed);
    } else {
        player.body.setVelocityY(0);
    }

    // Auto-fire at nearest enemy
    const time = this.time.now;
    if (time > lastFired) {
        const nearestEnemy = findNearestEnemy();
        if (nearestEnemy) {
            fireProjectile.call(this, nearestEnemy);
            lastFired = time + 100; // Fire rate: 2 shots per second
        }
    }

    // Update enemies to follow player
    enemies.getChildren().forEach(enemy => {
        this.physics.moveToObject(enemy, player, 100);
    });
}

function spawnEnemy() {
    // Spawn enemy at random edge of screen
    let x, y;
    if (Math.random() < 0.5) {
        x = Math.random() < 0.5 ? 0 : config.width;
        y = Math.random() * config.height;
    } else {
        x = Math.random() * config.width;
        y = Math.random() < 0.5 ? 0 : config.height;
    }

    const enemy = this.add.sprite(x, y, 'enemy');
    enemy.setDisplaySize(32, 32); // Set enemy size
    this.physics.add.existing(enemy);
    enemies.add(enemy);
    enemy.health = 30;
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
    this.time.delayedCall(2000, () => {
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
    
    if (enemy.health <= 0) {
        enemy.destroy();
        score += 10;
        scoreText.setText('Score: ' + score);
    }
}

function hitPlayer(player, enemy) {
    enemy.destroy();
    player.health -= 10;
    healthText.setText('Health: ' + player.health);

    if (player.health <= 0) {
        gameOver = true;
        this.add.text(config.width/2, config.height/2, 'Game Over', {
            fontSize: '64px',
            fill: '#fff'
        }).setOrigin(0.5);
    }
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

function showQuestion() {
    const questions = [
        {
            type: 'debug',
            question: "What's wrong with: for(let i = 0; i <= arr.length; i++)",
            options: ["Should be <", "Should be >=", "Nothing wrong", "Should be ++i"],
            correct: 0,
            reward: 'laser' // Changed reward type to projectile name
        },
        {
            type: 'git',
            question: "Git command to create & switch to new branch?",
            options: ["git branch new", "git checkout -b new", "git switch new", "git create new"],
            correct: 1,
            reward: 'plasma' // Changed reward type to projectile name
        }
    ];

    const question = questions[Math.floor(Math.random() * questions.length)];
    
    const quizDiv = document.createElement('div');
    quizDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        z-index: 1000;
        color: black;
    `;
    
    quizDiv.innerHTML = `
        <h3>${question.question}</h3>
        <p style="color: #666;">Question Type: ${question.type}</p>
        ${question.options.map((opt, i) => `
            <button onclick="answerQuestion(${i}, ${question.correct}, '${question.reward}', this)"
                    style="display: block; width: 100%; margin: 10px 0; padding: 10px;">
                ${opt}
            </button>
        `).join('')}
    `;
    
    document.body.appendChild(quizDiv);
}

// Add this to window scope so the onclick can access it
window.answerQuestion = function(selected, correct, reward, button) {
    if (selected === correct) {
        // Update projectile type based on question reward
        currentProjectileType = reward;
        
        // Show feedback
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 5px;
            animation: fadeOut 2s forwards;
        `;
        feedback.textContent = `Upgraded to ${reward} projectile!`;
        document.body.appendChild(feedback);
        
        setTimeout(() => feedback.remove(), 2000);
    }
    // Remove quiz UI
    button.parentElement.remove();
};

new Phaser.Game(config);