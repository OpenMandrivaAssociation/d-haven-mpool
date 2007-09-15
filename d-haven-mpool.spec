# Copyright (c) 2000-2007, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
%define _with_gcj_support 1
%define _without_maven 1
%define gcj_support %{?_with_gcj_support:1}%{!?_with_gcj_support:%{?_without_gcj_support:0}%{!?_without_gcj_support:%{?_gcj_support:%{_gcj_support}}%{!?_gcj_support:0}}}

# If you don't want to build with maven, and use straight ant instead,
# give rpmbuild option '--without maven'

%define with_maven %{!?_without_maven:1}%{?_without_maven:0}
%define without_maven %{?_without_maven:1}%{!?_without_maven:0}

%define section free

Name:           d-haven-mpool
Version:        1.0
Release:        %mkrel 3.0.3
Epoch:          0
Summary:        D-Haven Managed Pool async
License:        Apache Software License
Url:            http://d-haven.org/
Group:          Development/Java
Source0:        d-haven-mpool-1.0-src.tar.gz
#cvs -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/d-haven login
#cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/d-haven co -P managed-pool

Source1:        pom-maven2jpp-depcat.xsl
Source2:        pom-maven2jpp-newdepmap.xsl
Source3:        pom-maven2jpp-mapdeps.xsl
Source4:        d-haven-mpool-1.0-jpp-depmap.xml
Source5:        d-haven-mpool-1.0.pom
Patch0:         d-haven-mpool-1.0-build_xml.patch

Requires:       concurrent
Requires:       d-haven-event
BuildRequires:  jpackage-utils >= 0:1.7.2
BuildRequires:  ant >= 0:1.6.5
BuildRequires:  junit
%if %{with_maven}
BuildRequires:  maven >= 0:1.1
BuildRequires:  saxon
BuildRequires:  saxon-scripts
%endif
BuildRequires:  concurrent
BuildRequires:  d-haven-event
Requires(post):    jpackage-utils >= 0:1.7.2
Requires(postun):  jpackage-utils >= 0:1.7.2
%if %{gcj_support}
BuildRequires:    java-gcj-compat-devel
%endif

%if ! %{gcj_support}
BuildArch:      noarch
%endif

BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot

%description
D-Haven Managed Pool is a library designed to provide pools
that are asynchronously managed in a background thread.  The
pool system is very flexible and can accommodate just about
every need.  It boasts the ability to add pool listeners so
that you can instrument and intercept the pooled objects when
they are created, destroyed, acquired, and released.

%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java
Requires(post):   /bin/rm,/bin/ln
Requires(postun): /bin/rm

%description javadoc
%{summary}.

%if %{with_maven}
%package manual
Summary:        Documents for %{name}
Group:          Development/Documentation

%description manual
%{summary}.
%endif

%prep
%setup -q -n managed-pool
find . -name "*.jar" -exec rm -f {} \;
#for j in $(find . -name "*.jar"); do
#    mv $j $j.no
#done
%patch -b .sav

%build
%if %{with_maven}
export DEPCAT=$(pwd)/d-haven-mpool-1.0-depcat.new.xml
echo '<?xml version="1.0" standalone="yes"?>' > $DEPCAT
echo '<depset>' >> $DEPCAT
for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    /usr/bin/saxon project.xml %{SOURCE1} >> $DEPCAT
    popd
done
echo >> $DEPCAT
echo '</depset>' >> $DEPCAT
/usr/bin/saxon $DEPCAT %{SOURCE2} > d-haven-mpool-1.0-depmap.new.xml


for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    cp project.xml project.xml.orig
    /usr/bin/saxon -o project.xml project.xml.orig %{SOURCE3} map=%{SOURCE4}
    popd
done

maven \
      -Dmaven.javadoc.source=1.4 \
      -Dmaven.repo.remote=file:/usr/share/maven/repository \
      -Dmaven.home.local=$(pwd)/.maven \
      jar javadoc xdoc:transform
%else
export CLASSPATH=$(build-classpath concurrent d-haven-event junit)
CLASSPATH=${CLASSPATH}:target/classes:target/test-classes
%{ant} \
    -Dsource=1.4 \
    -Dbuild.sysclasspath=only \
    jar javadoc
%endif


%install
rm -rf $RPM_BUILD_ROOT
# jars
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}
install -m 644 target/managed-pool-1.0.jar \
$RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar

(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}*; do \
ln -sf ${jar} ${jar/-%{version}/}; done)

%add_to_maven_depmap %{name} managed-pool %{version} JPP %{name}

# poms
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/maven2/poms
install -pm 644 %{SOURCE5} \
    $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP.%{name}.pom

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
cp -pr target/docs/apidocs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name} # ghost symlink
rm -rf target/docs/apidocs

## manual
install -d -m 755 $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
cp -p LICENSE.txt $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
%if %{with_maven}
cp -pr target/docs/* $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
%endif

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
%update_maven_depmap
%if %{gcj_support}
if [ -x %{_bindir}/rebuild-gcj-db ]
then
  %{_bindir}/rebuild-gcj-db
fi
%endif

%postun
%update_maven_depmap
%if %{gcj_support}
if [ -x %{_bindir}/rebuild-gcj-db ]
then
  %{_bindir}/rebuild-gcj-db
fi
%endif

%files
%defattr(0644,root,root,0755)
%{_docdir}/%{name}-%{version}/LICENSE.txt
%{_javadir}/*
%{_datadir}/maven2/poms/*
%config(noreplace) %{_mavendepmapfragdir}/*
%if %{gcj_support}
%dir %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/%{name}-*%{version}.jar.*
%endif

%files javadoc
%defattr(0644,root,root,0755)
%{_javadocdir}/%{name}-%{version}
%{_javadocdir}/%{name}

%if %{with_maven}
%files manual
%defattr(0644,root,root,0755)
%{_docdir}/%{name}-%{version}
%endif
