const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Building Kortix Electron app...\n');

// Check if we're in the right directory
if (!fs.existsSync('package.json')) {
  console.error('❌ Please run this script from the frontend directory');
  process.exit(1);
}

// Step 1: Move all problematic directories completely outside src to avoid build errors
console.log('📦 Preparing for export build...');
try {
  // Move API directory
  const apiDir = 'src/app/api';
  const apiBackupDir = '../api_backup';
  
  if (fs.existsSync(apiDir)) {
    if (fs.existsSync(apiBackupDir)) {
      fs.rmSync(apiBackupDir, { recursive: true, force: true });
    }
    fs.renameSync(apiDir, apiBackupDir);
    console.log('✅ API directory moved outside src');
  }
  
  // Move auth callback directory
  const authCallbackDir = 'src/app/auth/callback';
  const authCallbackBackupDir = '../auth_callback_backup';
  
  if (fs.existsSync(authCallbackDir)) {
    if (fs.existsSync(authCallbackBackupDir)) {
      fs.rmSync(authCallbackBackupDir, { recursive: true, force: true });
    }
    fs.renameSync(authCallbackDir, authCallbackBackupDir);
    console.log('✅ Auth callback directory moved outside src');
  }
  
  // Move agents preview directory
  const agentsPreviewDir = 'src/app/agents/preview';
  const agentsPreviewBackupDir = '../agents_preview_backup';
  
  if (fs.existsSync(agentsPreviewDir)) {
    if (fs.existsSync(agentsPreviewBackupDir)) {
      fs.rmSync(agentsPreviewBackupDir, { recursive: true, force: true });
    }
    fs.renameSync(agentsPreviewDir, agentsPreviewBackupDir);
    console.log('✅ Agents preview directory moved outside src');
  }

  // Move opengraph-image file (causes issues with export)
  const opengraphImageFile = 'src/app/opengraph-image.tsx';
  const opengraphImageBackup = '../opengraph-image_backup.tsx';

  if (fs.existsSync(opengraphImageFile)) {
    if (fs.existsSync(opengraphImageBackup)) {
      fs.rmSync(opengraphImageBackup, { recursive: true, force: true });
    }
    fs.renameSync(opengraphImageFile, opengraphImageBackup);
    console.log('✅ OpenGraph image file moved outside src');
  }

  // Replace Server Actions with stubs (not supported with static export)
  const actionsDir = 'src/lib/actions';
  const actionsBackupDir = '../actions_backup';
  const actionsStubsDir = '../actions_stubs';
  
  if (fs.existsSync(actionsDir)) {
    // Backup original actions
    if (fs.existsSync(actionsBackupDir)) {
      fs.rmSync(actionsBackupDir, { recursive: true, force: true });
    }
    fs.renameSync(actionsDir, actionsBackupDir);
    console.log('✅ Server Actions directory backed up');
    
    // Copy stubs
    if (fs.existsSync(actionsStubsDir)) {
      fs.cpSync(actionsStubsDir, actionsDir, { recursive: true });
      console.log('✅ Server Actions stubs installed');
    }
  }

  // Move problematic dynamic route pages that can't be static exported
  const problematicPages = [
    'src/app/templates/[shareId]/page.tsx',
    'src/app/agents/preview/[templateId]/page.tsx',
    'src/app/(dashboard)/agents/config/[agentId]/workflow/[workflowId]/page.tsx',
    'src/app/(dashboard)/agents/config/[agentId]/page.tsx',
    'src/app/(dashboard)/agents/[threadId]/page.tsx',
    'src/app/(dashboard)/projects/[projectId]/thread/[threadId]/page.tsx',
    'src/app/(dashboard)/(teamAccount)/[accountSlug]/page.tsx',
    'src/app/(dashboard)/(teamAccount)/[accountSlug]/settings/page.tsx',
    'src/app/(dashboard)/(teamAccount)/[accountSlug]/settings/members/page.tsx',
    'src/app/(dashboard)/(teamAccount)/[accountSlug]/settings/billing/page.tsx'
  ];

  for (const pagePath of problematicPages) {
    const backupPath = `../${path.basename(pagePath)}_backup.tsx`;
    if (fs.existsSync(pagePath)) {
      if (fs.existsSync(backupPath)) {
        fs.rmSync(backupPath, { recursive: true, force: true });
      }
      fs.renameSync(pagePath, backupPath);
      console.log(`✅ ${pagePath} moved outside src`);
    }
  }
} catch (error) {
  console.error('❌ Failed to prepare directories:', error.message);
}

// Step 2: Build Next.js app with export mode
console.log('📦 Building Next.js application for export...');
try {
  execSync('NEXT_OUTPUT=export npm run build', { stdio: 'inherit' });
  console.log('✅ Next.js build completed');
} catch (error) {
  console.error('❌ Next.js build failed:', error.message);
  
  // Restore directories on failure
  try {
    // Restore API directory
    const apiDir = 'src/app/api';
    const apiBackupDir = '../api_backup';
    if (fs.existsSync(apiBackupDir)) {
      if (fs.existsSync(apiDir)) {
        fs.rmSync(apiDir, { recursive: true, force: true });
      }
      fs.renameSync(apiBackupDir, apiDir);
      console.log('✅ API directory restored');
    }
    
    // Restore auth callback directory
    const authCallbackDir = 'src/app/auth/callback';
    const authCallbackBackupDir = '../auth_callback_backup';
    if (fs.existsSync(authCallbackBackupDir)) {
      if (fs.existsSync(authCallbackDir)) {
        fs.rmSync(authCallbackDir, { recursive: true, force: true });
      }
      fs.renameSync(authCallbackBackupDir, authCallbackDir);
      console.log('✅ Auth callback directory restored');
    }
    
    // Restore agents preview directory
    const agentsPreviewDir = 'src/app/agents/preview';
    const agentsPreviewBackupDir = '../agents_preview_backup';
    if (fs.existsSync(agentsPreviewBackupDir)) {
      if (fs.existsSync(agentsPreviewDir)) {
        fs.rmSync(agentsPreviewDir, { recursive: true, force: true });
      }
      fs.renameSync(agentsPreviewBackupDir, agentsPreviewDir);
      console.log('✅ Agents preview directory restored');
    }

    // Restore Server Actions directory
    const actionsDir = 'src/lib/actions';
    const actionsBackupDir = '../actions_backup';
    if (fs.existsSync(actionsBackupDir)) {
      if (fs.existsSync(actionsDir)) {
        fs.rmSync(actionsDir, { recursive: true, force: true });
      }
      fs.renameSync(actionsBackupDir, actionsDir);
      console.log('✅ Server Actions directory restored');
    }

    // Restore opengraph-image file
    const opengraphImageFile = 'src/app/opengraph-image.tsx';
    const opengraphImageBackup = '../opengraph-image_backup.tsx';
    if (fs.existsSync(opengraphImageBackup)) {
      if (fs.existsSync(opengraphImageFile)) {
        fs.rmSync(opengraphImageFile, { recursive: true, force: true });
      }
      fs.renameSync(opengraphImageBackup, opengraphImageFile);
      console.log('✅ OpenGraph image file restored');
    }

    // Restore problematic dynamic route pages
    const problematicPages = [
      'src/app/templates/[shareId]/page.tsx',
      'src/app/agents/preview/[templateId]/page.tsx',
      'src/app/(dashboard)/agents/config/[agentId]/workflow/[workflowId]/page.tsx',
      'src/app/(dashboard)/agents/config/[agentId]/page.tsx',
      'src/app/(dashboard)/agents/[threadId]/page.tsx',
      'src/app/(dashboard)/projects/[projectId]/thread/[threadId]/page.tsx',
      'src/app/(dashboard)/(teamAccount)/[accountSlug]/settings/billing/page.tsx'
    ];

    for (const pagePath of problematicPages) {
      const backupPath = `../${path.basename(pagePath)}_backup.tsx`;
      if (fs.existsSync(backupPath)) {
        if (fs.existsSync(pagePath)) {
          fs.rmSync(pagePath, { recursive: true, force: true });
        }
        fs.renameSync(backupPath, pagePath);
        console.log(`✅ ${pagePath} restored`);
      }
    }
  } catch (restoreError) {
    console.error('❌ Failed to restore directories:', restoreError.message);
  }
  
  process.exit(1);
}

// Step 3: Restore directories after successful build
try {
  // Restore API directory
  const apiDir = 'src/app/api';
  const apiBackupDir = '../api_backup';
  if (fs.existsSync(apiBackupDir)) {
    if (fs.existsSync(apiDir)) {
      fs.rmSync(apiDir, { recursive: true, force: true });
    }
    fs.renameSync(apiBackupDir, apiDir);
    console.log('✅ API directory restored');
  }
  
  // Restore auth callback directory
  const authCallbackDir = 'src/app/auth/callback';
  const authCallbackBackupDir = '../auth_callback_backup';
  if (fs.existsSync(authCallbackBackupDir)) {
    if (fs.existsSync(authCallbackDir)) {
      fs.rmSync(authCallbackDir, { recursive: true, force: true });
    }
    fs.renameSync(authCallbackBackupDir, authCallbackDir);
    console.log('✅ Auth callback directory restored');
  }
  
  // Restore agents preview directory
  const agentsPreviewDir = 'src/app/agents/preview';
  const agentsPreviewBackupDir = '../agents_preview_backup';
  if (fs.existsSync(agentsPreviewBackupDir)) {
    if (fs.existsSync(agentsPreviewDir)) {
      fs.rmSync(agentsPreviewDir, { recursive: true, force: true });
    }
    fs.renameSync(agentsPreviewBackupDir, agentsPreviewDir);
    console.log('✅ Agents preview directory restored');
  }

  // Restore Server Actions directory
  const actionsDir = 'src/lib/actions';
  const actionsBackupDir = '../actions_backup';
  if (fs.existsSync(actionsBackupDir)) {
    if (fs.existsSync(actionsDir)) {
      fs.rmSync(actionsDir, { recursive: true, force: true });
    }
    fs.renameSync(actionsBackupDir, actionsDir);
    console.log('✅ Server Actions directory restored');
  }

  // Restore opengraph-image file
  const opengraphImageFile = 'src/app/opengraph-image.tsx';
  const opengraphImageBackup = '../opengraph-image_backup.tsx';
  if (fs.existsSync(opengraphImageBackup)) {
    if (fs.existsSync(opengraphImageFile)) {
      fs.rmSync(opengraphImageFile, { recursive: true, force: true });
    }
    fs.renameSync(opengraphImageBackup, opengraphImageFile);
    console.log('✅ OpenGraph image file restored');
  }

  // Restore problematic dynamic route pages
  const problematicPages = [
    'src/app/templates/[shareId]/page.tsx',
    'src/app/agents/preview/[templateId]/page.tsx',
    'src/app/(dashboard)/agents/config/[agentId]/workflow/[workflowId]/page.tsx',
    'src/app/(dashboard)/agents/config/[agentId]/page.tsx',
    'src/app/(dashboard)/agents/[threadId]/page.tsx',
    'src/app/(dashboard)/projects/[projectId]/thread/[threadId]/page.tsx',
    'src/app/(dashboard)/(teamAccount)/[accountSlug]/settings/billing/page.tsx'
  ];

  for (const pagePath of problematicPages) {
    const backupPath = `../${path.basename(pagePath)}_backup.tsx`;
    if (fs.existsSync(backupPath)) {
      if (fs.existsSync(pagePath)) {
        fs.rmSync(pagePath, { recursive: true, force: true });
      }
      fs.renameSync(backupPath, pagePath);
      console.log(`✅ ${pagePath} restored`);
    }
  }
} catch (error) {
  console.error('❌ Failed to restore directories:', error.message);
}

// Step 2: Check if electron-builder is installed
console.log('🔍 Checking electron-builder...');
try {
  execSync('npx electron-builder --version', { stdio: 'inherit' });
} catch (error) {
  console.log('📦 Installing electron-builder...');
  execSync('npm install electron-builder --save-dev', { stdio: 'inherit' });
}

// Step 3: Build Electron app
console.log('⚡ Building Electron application...');
try {
  const platform = process.argv[2] || 'current';
  let buildCommand = 'npx electron-builder';
  
  if (platform !== 'current') {
    buildCommand += ` --${platform}`;
  }
  
  // Build unpacked directory to avoid native module issues
  buildCommand += ' --dir';
  
  execSync(buildCommand, { stdio: 'inherit' });
  console.log('✅ Electron build completed');
} catch (error) {
  console.error('❌ Electron build failed:', error.message);
  process.exit(1);
}

console.log('\n🎉 Kortix Electron app built successfully!');
console.log('📁 Check the dist-electron directory for the built application');